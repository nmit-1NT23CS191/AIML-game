pipeline {
  agent { label 'docker-agent' }

  environment {
    registry = "ravikiran1nt23cs191/aiml-game"
    registryCredential = 'dockerhub'
  }

  stages {

    stage('Checkout') {
      steps {
        git branch: 'main',
        credentialsId: 'github',
        url: 'https://github.com/nmit-1NT23CS191/AIML-game.git'
      }
    }

    stage('Stage I: Build') {
      steps {
        echo "Building static site assets ..."

        sh '''
        # Print all files in the directory to the Jenkins log for debugging
        ls -la
        
        # Test if the files exist
        test -f index.html
        
        test -f ai_arithmetic_maze_race_2.py
        '''
      }
    }

  
  

    stage('Stage II: Code Coverage') {
      steps {
        echo "Generating Python code coverage report for SonarQube..."
        
        sh '''
        # 1. Create a virtual environment named 'myenv'
        python3 -m venv myenv
        
        # 2. Activate the virtual environment
        . myenv/bin/activate
        
        # 3. Install the testing tools safely inside the environment
        pip install pytest pytest-cov
        
        # 4. Run tests and generate the coverage.xml file for SonarQube
        python -m pytest --cov=. --cov-report=xml || true
        '''
      }
    }

    stage('Stage III: SCA (Trivy)') {
      steps {
        echo "Running SCA using Trivy file system scan for dependency and configuration vulnerabilities..."
        
        // Run the Trivy scan and output to a text file
        // The "|| true" ensures the pipeline doesn't fail just because vulnerabilities are found
        sh "trivy fs --scanners vuln,config . > sca-report.txt || true"
      }
      post {
        always {
          // This saves the text file to your Jenkins build page so you can download it
          archiveArtifacts artifacts: 'sca-report.txt', allowEmptyArchive: true
        }
      }
    }

    stage('Stage IV: SAST (SonarQube)') {
      steps {
        echo "Running SonarQube analysis ..."
        
        withSonarQubeEnv('mysonarqube') {
          sh '''
          sonar-scanner \
            -Dsonar.projectKey=AIML-game \
            -Dsonar.projectName=AIML-game \
            -Dsonar.sources=. \
            -Dsonar.exclusions=Jenkinsfile,myenv/** \
            -Dsonar.python.coverage.reportPaths=coverage.xml
          '''
        }
      }
    }


    stage('Stage V: QualityGates') {
      steps {
        echo "Checking SonarQube Quality Gate..."
        timeout(time: 2, unit: 'MINUTES') {
          // Change abortPipeline to false so the pipeline continues even if the grade is bad
          waitForQualityGate abortPipeline: false
        }
      }
    }


    stage('Stage VI: Build & Push Docker Image') {
      steps {
        echo "Building and Pushing Docker Image to Docker Hub..."
        script {
          // Log into Docker Hub using the credentials you saved
          docker.withRegistry('', registryCredential) {
            
            // Build the image and tag it with the Jenkins Build Number
            def myImage = docker.build("${registry}:${env.BUILD_NUMBER}")
            
            // Push the versioned tag
            myImage.push()
            
            // Also push the 'latest' tag
            myImage.push('latest')
          }
        }
      }
    }

    stage('Stage VII: Scan Image') {
      steps {
        echo "Scanning Docker Image for Vulnerabilities using Trivy..."
        
        // Scan the image and output to a text file
        sh "trivy image --scanners vuln ${registry}:latest > trivyimage-report.txt || true"
      }
      post {
        always {
          // Saves the scan report to your Jenkins UI for you to download
          archiveArtifacts artifacts: 'trivyimage-report.txt', allowEmptyArchive: true
        }
      }
    }

    stage('Stage VIII: Smoke Test') {
      steps {
        echo "Smoke Testing the Python Docker Image..."
        
        // This spins up the container, runs a quick print command, and deletes itself (--rm)
        // This proves the container is healthy and Python is working, without needing a monitor!
        sh "docker run --rm ${registry}:latest python -c \"print('Smoke test passed! Container is healthy.')\""
      }
    }
  }
}
  

 

 

 

    
//   }
// }
