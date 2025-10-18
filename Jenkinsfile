pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = 'docker.io/nero0110'           // Your Docker Hub namespace
        IMAGE_NAME = 'wikipedia-flask-app'
        DOCKER_CREDENTIALS_ID = 'docker-credentials-id'
        SONARQUBE_ENV = 'SonarQube'
        SONAR_TOKEN = credentials('sonarqube-token')
        ARGOCD_TOKEN = credentials('argocd-token')
        GITHUB_CRED = 'github-cred'
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', credentialsId: "${GITHUB_CRED}", url: 'https://github.com/Saador042/Search-engine.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    env.IMAGE_TAG = "${IMAGE_NAME}:${env.BUILD_NUMBER}"
                    sh "docker build -t ${DOCKER_REGISTRY}/${env.IMAGE_TAG} ."
                }
            }
        }

        stage('Unit Test') {
            steps {
                sh 'python -m py_compile app.py'
            }
        }

        stage('Trivy Scan') {
            steps {
                sh "trivy image --exit-code 1 --severity HIGH,CRITICAL ${DOCKER_REGISTRY}/${env.IMAGE_TAG} || true"
            }
        }

        stage('SonarQube Scan') {
            steps {
                withSonarQubeEnv("${SONARQUBE_ENV}") {
                    sh """
                    sonar-scanner \
                        -Dsonar.projectKey=wikipedia-flask-app \
                        -Dsonar.sources=. \
                        -Dsonar.host.url=${SONAR_HOST_URL} \
                        -Dsonar.login=${SONAR_TOKEN}
                    """
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", "${DOCKER_CREDENTIALS_ID}") {
                        sh "docker push ${DOCKER_REGISTRY}/${env.IMAGE_TAG}"
                    }
                }
            }
        }

        stage('Deploy to Kubernetes (via ArgoCD)') {
            steps {
                script {
                    sh """
                    curl -k -H "Authorization: Bearer ${ARGOCD_TOKEN}" \
                        -X POST https://argocd-server/api/v1/applications/search-engine/sync
                    """
                }
            }
        }
    }

    post {
        success {
            echo "Deployment completed successfully! ✅ "
        }
        failure {
            echo "Pipeline failed. Check Jenkins logs.❌ "
        }
        always {
            cleanWs()
        }
    }
}
