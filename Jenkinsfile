pipeline {
    agent any
    environment {
        DOCKER_REGISTRY = 'localhost:5000'          // Replace with your registry URL
        IMAGE_NAME = 'wikipedia-flask-app'          // Your Docker image name
        DOCKER_CREDENTIALS_ID = 'docker-credentials-id' // Jenkins Docker credentials ID
        SONARQUBE_ENV = 'SonarQube'                 // SonarQube server configured in Jenkins
    }
    stages {
        stage('Checkout') {
            steps {
                echo "Cloning GitHub repository..."
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    def IMAGE_TAG = "${IMAGE_NAME}:${env.GIT_COMMIT}"
                    docker.build(IMAGE_TAG)
                    env.IMAGE_TAG = IMAGE_TAG
                }
            }
        }

        stage('Unit Test') {
            steps {
                echo "Running basic Python syntax test..."
                sh 'python -m py_compile app.py'
            }
        }

        stage('Trivy Scan') {
            steps {
                echo "Scanning Docker image for vulnerabilities..."
                sh """
                    trivy image --severity HIGH,CRITICAL ${env.IMAGE_TAG} || exit 1
                """
            }
        }

        stage('SonarQube Scan') {
            steps {
                echo "Running SonarQube code quality scan..."
                withSonarQubeEnv("${SONARQUBE_ENV}") {
                    sh "sonar-scanner -Dsonar.projectKey=wikipedia-flask-app -Dsonar.sources=."
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                echo "Pushing Docker image to registry..."
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", "${DOCKER_CREDENTIALS_ID}") {
                        docker.image("${env.IMAGE_TAG}").push()
                    }
                }
            }
        }
    }

    post {
        always {
            echo "Cleaning workspace..."
            cleanWs()
        }
        success {
            echo "Pipeline completed successfully!"
        }
        failure {
            echo "Pipeline failed!"
        }
    }
}
