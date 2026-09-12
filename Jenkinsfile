pipeline {
    agent any

    environment {
        NET             = 'examen-secnet'
        TARGET_IMAGE    = 'juice-shop-target:pipeline'
        TARGET_NAME     = 'juice-shop-under-test'
        WORKDIR         = '/workspace'
        REPORTS_DIR     = '/workspace/reports'
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Checkout du code source (déjà présent dans le workspace monté).'
                sh 'ls -la ${WORKDIR}/juice-shop | head -20'
            }
        }

        stage('Build / Preparation') {
            steps {
                echo 'Construction de l\'image Docker de l\'application cible (Juice Shop).'
                sh '''
                    docker build -t ${TARGET_IMAGE} ${WORKDIR}/juice-shop
                    docker rm -f ${TARGET_NAME} || true
                    docker run -d --name ${TARGET_NAME} --network ${NET} ${TARGET_IMAGE}

                    echo "Attente du démarrage de l'application..."
                    for i in $(seq 1 30); do
                        if docker run --rm --network ${NET} curlimages/curl:8.10.1 -sf http://${TARGET_NAME}:3000/ > /dev/null 2>&1; then
                            echo "Application prête."
                            break
                        fi
                        sleep 2
                    done
                '''
            }
        }

        stage('Security Analysis') {
            parallel {
                stage('SAST - Semgrep') {
                    steps {
                        sh '''
                            mkdir -p ${REPORTS_DIR}
                            semgrep --config p/owasp-top-ten --config p/javascript --config p/typescript \
                                --json --output ${REPORTS_DIR}/semgrep-report.json \
                                ${WORKDIR}/juice-shop/routes ${WORKDIR}/juice-shop/lib ${WORKDIR}/juice-shop/frontend/src || true
                        '''
                    }
                }
                stage('SCA - Trivy') {
                    steps {
                        sh '''
                            mkdir -p ${REPORTS_DIR}
                            trivy fs --scanners vuln --format json \
                                --output ${REPORTS_DIR}/trivy-report.json \
                                ${WORKDIR}/juice-shop || true
                        '''
                    }
                }
                stage('Secret Detection - Gitleaks') {
                    steps {
                        sh '''
                            mkdir -p ${REPORTS_DIR}
                            gitleaks detect --source ${WORKDIR}/juice-shop --no-git \
                                --report-format json --report-path ${REPORTS_DIR}/gitleaks-report.json --exit-code 0
                        '''
                    }
                }
            }
        }

        stage('Additional Security Check - DAST (OWASP ZAP)') {
            steps {
                sh '''
                    mkdir -p ${REPORTS_DIR}
                    docker run --rm --network ${NET} \
                        -v ${REPORTS_DIR}:/zap/wrk/:rw \
                        -t zaproxy/zap-stable zap-baseline.py \
                        -t http://${TARGET_NAME}:3000 \
                        -J zap-report.json -r zap-report.html -w zap-report.md || true
                '''
            }
        }

        stage('Report Generation') {
            steps {
                sh 'python3 ${WORKDIR}/scripts/aggregate_report.py'
            }
        }

        stage('Notification') {
            steps {
                sh '''
                    echo "=== Résumé du pipeline de sécurité ==="
                    cat ${REPORTS_DIR}/summary.md || true
                    echo "Notification envoyée (simulation) : équipe sécurité + équipe dev."
                '''
            }
        }
    }

    post {
        always {
            sh 'docker rm -f ${TARGET_NAME} || true'
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
    }
}
