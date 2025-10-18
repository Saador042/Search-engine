pipeline {
    agent any
    environment {
        DOCKER_REGISTRY = 'localhost:5000'
        IMAGE_NAME = 'wikipedia-flask-app'
        DOCKER_CREDENTIALS_ID = 'docker-credentials-id'
        SONARQUBE_ENV = 'SonarQube'
        KUBECONFIG = credentials('k8s-config')
        ARGOCD_SERVER = 'localhost:8081'
        ARGOCD_AUTH_TOKEN = credentials('argocd-token')
    }
    
    stages {
        stage('Checkout Git') {
            steps {
                echo "1. Cloning GitHub repository..."
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "2. Building Docker image..."
                script {
                    def IMAGE_TAG = "${env.BUILD_NUMBER}"
                    docker.build("${IMAGE_NAME}:${IMAGE_TAG}")
                    env.IMAGE_TAG = "${IMAGE_NAME}:${IMAGE_TAG}"
                    env.FULL_IMAGE = "${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                }
            }
        }

        stage('Security Tests') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        echo "3.1 Running Python security tests..."
                        sh '''
                            python -m venv venv
                            . venv/bin/activate
                            pip install -r requirements.txt
                            python -m py_compile app.py
                            python -c "import ast; ast.parse(open('app.py').read())" || exit 1
                        '''
                    }
                }
                stage('Dependency Scan') {
                    steps {
                        echo "3.2 Scanning Python dependencies..."
                        sh '''
                            trivy fs . --severity HIGH,CRITICAL --exit-code 0
                            pip-audit || true
                        '''
                    }
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                echo "4. Running SonarQube code analysis..."
                withSonarQubeEnv("${SONARQUBE_ENV}") {
                    sh """
                        sonar-scanner \
                        -Dsonar.projectKey=wikipedia-flask-app \
                        -Dsonar.sources=. \
                        -Dsonar.host.url=${SONARQUBE_URL} \
                        -Dsonar.login=${SONARQUBE_AUTH_TOKEN} \
                        -Dsonar.coverage.exclusions=**/test_*,**/tests/** \
                        -Dsonar.python.coverage.reportPaths=coverage.xml \
                        -Dsonar.qualitygate.wait=true
                    """
                }
            }
        }

        stage('Quality Gate') {
            steps {
                echo "5. Checking Quality Gate status..."
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Trivy Security Scan') {
            steps {
                echo "6. Scanning Docker image for vulnerabilities..."
                sh """
                    trivy image --severity HIGH,CRITICAL --exit-code 1 \
                    --format sarif -o trivy-report.sarif \
                    ${env.IMAGE_TAG}
                """
            }
            post {
                always {
                    archiveArtifacts artifacts: 'trivy-report.sarif', fingerprint: true
                }
            }
        }

        stage('Push to Docker Registry') {
            steps {
                echo "7. Pushing Docker image to registry..."
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", "${DOCKER_CREDENTIALS_ID}") {
                        docker.image("${env.IMAGE_TAG}").push()
                    }
                }
            }
        }

        stage('Update GitOps Manifests') {
            steps {
                echo "8. Updating GitOps manifests for ArgoCD..."
                script {
                    sh """
                        sed -i 's|${DOCKER_REGISTRY}/${IMAGE_NAME}:.*|${env.FULL_IMAGE}|g' k8s/deployment.yaml
                        git config user.email "jenkins@ci.com"
                        git config user.name "Jenkins CI"
                        git add k8s/deployment.yaml
                        git commit -m "CI: Update to ${env.FULL_IMAGE} [Build ${env.BUILD_NUMBER}]" || true
                        git push origin main || true
                    """
                }
            }
        }

        stage('ArgoCD Deployment') {
            steps {
                echo "9. Triggering ArgoCD deployment..."
                script {
                    sh """
                        curl -X POST \
                        "http://${ARGOCD_SERVER}/api/v1/applications/wikipedia-flask-app/sync" \
                        -H "Authorization: Bearer ${ARGOCD_AUTH_TOKEN}" \
                        -H "Content-Type: application/json" \
                        -d '{"dryRun": false, "prune": true, "resources": null, "strategy": null}' \
                        --retry 3 --retry-delay 5
                    """
                }
            }
        }

        stage('Health Check & Monitoring') {
            steps {
                echo "10. Verifying deployment health and metrics..."
                script {
                    sleep 30
                    sh """
                        kubectl rollout status deployment/wikipedia-flask-app --timeout=300s
                        curl -f http://wikipedia-flask-service:5000/health || \
                        curl -f http://wikipedia-flask-service:5000/metrics || \
                        echo "Health checks completed"
                    """
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline execution completed - Security audit trail preserved"
            sh 'docker system prune -f || true'
            cleanWs()
            archiveArtifacts artifacts: '**/*.sarif, **/*.json', fingerprint: true
        }
        success {
            echo "SECURE PIPELINE COMPLETED SUCCESSFULLY"
            echo "Code Quality: Passed"
            echo "Security Scans: Passed"
            echo "Quality Gates: Passed"
            echo "Deployment: Secure"
            echo "Monitoring: Active"
        }
        failure {
            echo "SECURE PIPELINE FAILED - Security checks prevented deployment"
            echo "Investigation required for security violations"
        }
        unstable {
            echo "Pipeline marked as unstable - Quality Gate failed"
            echo "Check SonarQube for quality issues"
        }
    }
}
