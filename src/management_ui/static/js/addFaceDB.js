document.addEventListener("DOMContentLoaded", function() {
    let capturedImages = [];
    let student_id;

    function hideAllInstructions() {
        document.querySelectorAll('.instruction').forEach(function(element) {
            element.style.display = 'none';
        });
    }

    function generateRandomNumbers(length) {
        let numbers = '';
        for (let i = 0; i < length; i++) {
            numbers += Math.floor(Math.random() * 10);
        }
        return numbers;
    }

    function startInstructionSequence() {
        setTimeout(function() {
            hideAllInstructions();
            document.getElementById('instruction-1').style.display = 'block';
        }, 0);

        setTimeout(function() {
            hideAllInstructions();
            document.getElementById('instruction-2').style.display = 'block';
            captureImages(5);
        }, 2000);

        setTimeout(function() {
            hideAllInstructions();
            document.getElementById('instruction-3').style.display = 'block';
            captureImages(3);
        }, 6000);

        setTimeout(function() {
            hideAllInstructions();
            document.getElementById('instruction-4').style.display = 'block';
            captureImages(3);
        }, 10000);

        setTimeout(function() {
            hideAllInstructions();
            document.getElementById('instruction-5').style.display = 'block';
            captureImages(4);
        }, 14000);

        setTimeout(function() {
            hideAllInstructions();
            const instruction6 = document.getElementById('instruction-6');
            instruction6.style.display = 'block';
            const randomNumbers = generateRandomNumbers(5);
            const randomNumberElement = document.getElementById('random-numbers');
            randomNumberElement.innerText = randomNumbers;
            randomNumberElement.style.display = 'block';
            captureImages(5);

            setTimeout(function() {
                instruction6.style.display = 'none';
                randomNumberElement.style.display = 'none';
                showProgressModal();
                uploadImagesToFirebase();
            }, 5000);
        }, 18000);
    }

    function captureImages(count) {
        for (let i = 0; i < count; i++) {
            setTimeout(function() {
                fetch('/capture_image')
                    .then(response => response.json())
                    .then(data => {
                        if (data.filename) {
                            capturedImages.push(data.filename);
                        }
                        console.log('Image captured: ', data);
                    })
                    .catch(error => console.error('Error capturing image:', error));
            }, i * 1000);
        }
    }

    function showProgressModal() {
        const successModal = document.getElementById('success-modal');
        successModal.style.display = 'block';
        let width = 1;
        const progressBar = document.getElementById('progress-bar');
        const interval = setInterval(function() {
            if (width >= 100) {
                clearInterval(interval);
            } else {
                width++;
                progressBar.style.width = width + '%';
                progressBar.innerText = width + '%';
            }
        }, 200);
    }


    function uploadImagesToFirebase() {
        fetch('/upload_images', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                images: capturedImages.map(file_path => ({ file_path })),
                student_id: student_id
            }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Uploaded images: ', data);
            // Cập nhật thanh tiến trình lên 100% khi tải lên xong
            const progressBar = document.getElementById('progress-bar');
            progressBar.style.width = '100%';
            progressBar.innerText = '100%';
            setTimeout(function() {
                document.getElementById('progress-container').style.display = 'none';
                document.getElementById('progress-bar').style.display = 'none';
                document.querySelector('.modal-content .icon-success').style.display = 'block';
                document.querySelector('.modal-content p').style.display = 'block';
            }, 2000);
        })
        .catch(error => console.error('Error uploading images:', error));
    }


    // Hàm khởi tạo camera khi trang thêm ảnh sinh viên được tải
    function startCamera() {
        const videoElement = document.getElementById('video-feed');
        videoElement.src = '/video_feed';
        videoElement.play();
    }

    // Nếu bạn rời trang và quay lại, khởi tạo lại camera
    window.addEventListener('load', function() {
        startCamera();
    });

    // Khi bạn rời khỏi trang hoặc đóng modal, hãy tắt camera
    window.addEventListener('beforeunload', function() {
        fetch('/stop_camera')
            .then(response => response.json())
            .then(data => console.log(data))
            .catch(error => console.error('Error stopping camera:', error));
    });

    document.getElementById('info-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const name = document.getElementById('name').value;
        student_id = document.getElementById('student_id').value;
        const major = document.getElementById('class_name').value;

        document.getElementById('display-name').innerText = name;
        document.getElementById('display-student-id').innerText = student_id;
        document.getElementById('display-class-name').innerText = major;

        document.getElementById('info-form').style.display = 'none';
        document.querySelector('.info-display').style.display = 'block';
        startInstructionSequence();
    });
});




