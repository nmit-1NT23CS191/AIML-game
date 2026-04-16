pipeline {
  agent {label 'build'}

  environment {
    registry = "firstcicd"
    registryCredential = 'dockerhub'
  }


  stages {
    stage('Checkout') {
      steps {
         git branch: 'main', changelog: false, credentialsId: 'github', poll: false, url: 'https://github.com/nmit-1NT23CS191/AIML-game.git'
      }
    }
  


    stage('Stage I: Build') {
      steps {
        echo "Building static site assets ..."
        sh "test -f index.html && test -f style.css && test -f script.js"
      }
    }
  

    stage('Stage II: Code Coverage ') {
      steps {
        echo "Code coverage is not applicable for this static HTML/CSS/JS project."
      }
    }
  

    stage('Stage III: SCA') {
      steps {
        echo "Running SCA using Trivy file system scan for dependency and configuration vulnerabilities..."
        sh "trivy fs --scanners vuln,config . > sca-report.txt || true"
      }
    }
  

    stage('Stage IV: SAST') {
      steps {
        echo "Running SonarQube analysis ..."
        withSonarQubeEnv('mysonarqube') {
          sh "sonar-scanner -Dsonar.projectKey=AIML-game -Dsonar.projectName=AIML-game -Dsonar.sources=. -Dsonar.exclusions=Jenkinsfile"
        }
      }
    }

    stage('Stage V: QualityGates') {
      steps {
        echo "Checking SonarQube Quality Gate..."
        timeout(time: 2, unit: 'MINUTES') {
          waitForQualityGate abortPipeline: true
        }
      }
    }
  }
}

//     stage('Stage V: QualityGates') {
//       steps {
//         echo "Checking SonarQube Quality Gate..."
//         timeout(time: 2, unit: 'MINUTES') {
//           waitForQualityGate()
//         }
//       }
//     }

//     stage('Stage VI: Build Image') {
//       steps {
//         echo "Build Docker Image"
//         script {
//           docker.withRegistry('', registryCredential) {
//             myImage = docker.build registry
//             myImage.push()
//           }
//         }
//       }
//     }

//     stage('Stage VII: Scan Image ') {
//       steps {
//         echo "Scanning Image for Vulnerabilities"
//         sh "trivy image --scanners vuln ${registry}:latest > trivyresults.txt"
//       }
//     }

//     stage('Stage VIII: Smoke Test ') {
//       steps {
//         echo "Smoke Test the Image"
//         sh "docker run -d --name smokerun -p 8080:80 ${registry}:latest"
//         sh "sleep 10"
//         sh "curl -f http://localhost:8080 || exit 1"
//         sh "docker rm --force smokerun"
//       }
//     }
//   }
// }
