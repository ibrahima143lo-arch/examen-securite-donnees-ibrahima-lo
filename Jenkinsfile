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
                        if curl -sf http://${TARGET_NAME}:3000/ > /dev/null 2>&1; then
                            echo "Application prête."
                            break
                        fi
                        sleep 2
                    done
                '''
            }
        }

        // Note: these three run SEQUENTIALLY, not in parallel. On a resource-constrained
        // lab machine (8GB RAM total, most already claimed by the OS/Docker Desktop VM),
        // running Semgrep + Trivy (which also downloads/loads a ~110MB vulnerability DB on
        // first use) + Gitleaks concurrently pushed the Docker Desktop VM into repeated
        // out-of-memory crashes. Trading a bit of wall-clock time for stability here.
        stage('Security Analysis') {
            stages {
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
                // Two DooD gotchas fixed here:
                // 1) zap-baseline.py flat-out refuses to run ("file based option specified but
                //    /zap/wrk is not mounted") unless /zap/wrk is an actual mount — a plain
                //    write-then-`docker cp` without any mount does not satisfy it.
                // 2) A host bind-mount ("-v ${REPORTS_DIR}:...") would be resolved by the
                //    *host's* Docker Desktop engine, which has no notion of "/workspace" (that
                //    path only exists inside the Jenkins container). A named Docker *volume*
                //    sidesteps this entirely — the daemon manages it directly, no host path
                //    translation involved — and `docker cp` afterwards reads through that mount
                //    and is written locally by the Jenkins container's own docker CLI.
                sh '''
                    mkdir -p ${REPORTS_DIR}
                    docker rm -f zap-scan || true
                    docker volume create zap-wrk >/dev/null
                    docker run --rm -v zap-wrk:/zap/wrk busybox chmod -R 777 /zap/wrk
                    docker run --name zap-scan --network ${NET} -v zap-wrk:/zap/wrk:rw \
                        zaproxy/zap-stable zap-baseline.py \
                        -t http://${TARGET_NAME}:3000 -m 2 \
                        -J zap-report.json -r zap-report.html -w zap-report.md || true
                    docker cp zap-scan:/zap/wrk/zap-report.json ${REPORTS_DIR}/zap-report.json || true
                    docker cp zap-scan:/zap/wrk/zap-report.html ${REPORTS_DIR}/zap-report.html || true
                    docker cp zap-scan:/zap/wrk/zap-report.md ${REPORTS_DIR}/zap-report.md || true
                    docker rm -f zap-scan || true
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
