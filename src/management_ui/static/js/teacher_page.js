$(document).ready(function () {
    let studentsDataByClass = []; // Biến lưu dữ liệu sinh viên theo lớp
    let classesDataBySubject = []; // Biến lưu dữ liệu lớp theo môn học

    // Hàm cập nhật URL khi chuyển trang
    function updateHistoryState(page, title, url) {
        history.pushState({ page: page }, title, url);
        localStorage.setItem('currentPage', page);
    }

    $('#manage-subjects').on('click', function (event) {
        event.preventDefault();
        $('#header-text').text('Danh sách các môn học');
        loadSubjects();
        localStorage.setItem('currentPage', 'subjects');
        updateHistoryState('subjects', 'Danh sách các môn học', '/subjects');
    });

    $('#manage-classes').on('click', function (event) {
        event.preventDefault();
        $('#header-text').text('Danh sách các lớp');
        loadClasses();
        localStorage.setItem('currentPage', 'classes');
        updateHistoryState('classes', 'Danh sách các lớp', '/classes');
    });

    $('#attendance-system').on('click', function (event) {
        event.preventDefault();
        fetch('/start-attendance')
            .then(response => {
                if (response.ok) {
                    alert('Đã mở hệ thống điểm danh.');
                } else {
                    alert('Không thể mở hệ thống điểm danh.');
                }
            })
            .catch(error => {
                console.error('Error starting attendance system:', error);
            });
    });



    $('#search-input').on('input', function () {
        let searchText = $(this).val().toLowerCase();
        if ($('#header-text').text() === 'Danh sách các môn học') {
            filterSubjects(searchText);
        } else if ($('#header-text').text() === 'Danh sách các lớp' || $('#header-text').text() === 'Danh sách các lớp trong môn học') {
            filterClasses(searchText);
        } else if ($('#header-text').text() === 'Danh sách sinh viên' || $('#header-text').text() === 'Danh sách sinh viên trong lớp') {
            filterStudents(searchText);
        }
    });

    function loadSubjects() {
        $('#content-area').html(`
            <table class="table" style="width: 100%;">
                <thead class="thead-light">
                    <tr>
                        <th scope="col">STT</th>
                        <th scope="col">Mã môn</th>
                        <th scope="col">Tên môn</th>
                        <th scope="col">Số lớp</th>
                        <th scope="col">Action</th>
                    </tr>
                </thead>
                <tbody id="subjects-table-body">
                </tbody>
            </table>
        `);
        fetch('/subjects').then(response => response.json()).then(data => {
            window.subjectsData = data; // Lưu dữ liệu vào biến toàn cục để sử dụng cho tìm kiếm
            displaySubjects(data);
        });
    }

    function loadClasses() {
        $('#content-area').html(`
            <table class="table" style="width: 100%;">
                <thead class="thead-light">
                    <tr>
                        <th scope="col">STT</th>
                        <th scope="col">Mã lớp</th>
                        <th scope="col">Tên môn</th>
                        <th scope="col">Ca học</th>
                        <th scope="col">Thứ</th>
                        <th scope="col">Thời gian học</th>
                        <th scope="col">Giảng viên</th>
                        <th scope="col">Action</th>
                    </tr>
                </thead>
                <tbody id="classes-table-body">
                </tbody>
            </table>
        `);
        fetch('/classes').then(response => response.json()).then(data => {
            window.classesData = data;
            displayClasses(data);
        });
    }

    function loadClassesBySubject(subjectId) {
        fetch(`/subjects/${subjectId}/classes`)
            .then(response => response.json())
            .then(data => {
                classesDataBySubject = data;
                displayClassesBySubject(data);
                localStorage.setItem('currentPage', 'classesBySubject');
                localStorage.setItem('currentSubjectId', subjectId);
                updateHistoryState('classesBySubject', 'Danh sách các lớp trong môn học', `/subjects/${subjectId}/classes`);
            });
    }

    function loadStudentsByClass(classId) {
        fetch(`/classes/${classId}/students`)
            .then(response => response.json())
            .then(data => {
                studentsDataByClass = data;
                displayStudentsByClass(data);
                localStorage.setItem('currentPage', 'studentsByClass');
                localStorage.setItem('currentClassId', classId);
                updateHistoryState('studentsByClass', 'Danh sách sinh viên trong lớp', `/classes/${classId}/students`);
            });
    }

    function displaySubjects(data) {
        let rows = '';
        data.forEach((subject, index) => {
            rows += `
                <tr data-subject-id="${subject.id}">
                    <td>${index + 1}</td>
                    <td>${subject.id}</td>
                    <td>${subject.name}</td>
                    <td>${subject.classIDs.length}</td>
                    <td>
                        <button class="btn btn-outline-info"><i class="bi bi-pencil-square"></i></button>
                        <button class="btn btn-danger"><i class="bi bi-trash3-fill"></i></button>
                    </td>
                </tr>
            `;
        });
        $('#subjects-table-body').html(rows);

        // Thêm sự kiện click vào từng hàng
        $('#subjects-table-body tr').on('click', function () {
            let subjectId = $(this).data('subject-id');
            $('#header-text').text('Danh sách các lớp trong môn học');
            loadClassesBySubject(subjectId);
        });
    }

    function displayClasses(data) {
        let rows = '';
        data.forEach((cls, index) => {
            rows += `
                <tr data-class-id="${cls.id}">
                    <th scope="row">${index + 1}</th>
                    <td>${cls.id}</td>
                    <td>${cls.subjectName}</td>
                    <td>${cls.name}</td>
                    <td>${cls.day_of_week}</td>
                    <td>${cls.start_date} -> ${cls.end_date}</td>
                    <td>${cls.teacherName}</td>
                    <td>
                        <button class="btn btn-outline-info"><i class="bi bi-pencil-square"></i></button>
                        <button class="btn btn-danger"><i class="bi bi-trash3-fill"></i></button>
                    </td>
                </tr>
            `;
        });
        $('#classes-table-body').html(rows);

        // Thêm sự kiện click vào từng hàng
        $('#classes-table-body tr').on('click', function () {
            let classId = $(this).data('class-id');
            $('#header-text').text('Danh sách sinh viên trong lớp');
            loadStudentsByClass(classId);
        });
    }

    function displayClassesBySubject(data) {
        let rows = '';
        data.forEach((cls, index) => {
            rows += `
                <tr data-class-id="${cls.id}">
                    <th scope="row">${index + 1}</th>
                    <td>${cls.id}</td>
                    <td>${cls.subjectName}</td>
                    <td>${cls.name}</td>
                    <td>${cls.day_of_week}</td>
                    <td>${cls.start_date} -> ${cls.end_date}</td>
                    <td>${cls.teacherName}</td>
                    <td>
                        <button class="btn btn-outline-info"><i class="bi bi-pencil-square"></i></button>
                        <button class="btn btn-danger"><i class="bi bi-trash3-fill"></i></button>
                    </td>
                </tr>
            `;
        });
        $('#content-area').html(`
            <table class="table" style="width: 100%;">
                <thead class="thead-light">
                    <tr>
                        <th scope="col">STT</th>
                        <th scope="col">Mã lớp</th>
                        <th scope="col">Tên môn</th>
                        <th scope="col">Ca học</th>
                        <th scope="col">Thứ</th>
                        <th scope="col">Thời gian học</th>
                        <th scope="col">Giảng viên</th>
                        <th scope="col">Action</th>
                    </tr>
                </thead>
                <tbody id="classes-table-body">
                    ${rows}
                </tbody>
            </table>
        `);

        // Thêm sự kiện click vào từng hàng
        $('#classes-table-body tr').on('click', function () {
            let classId = $(this).data('class-id');
            $('#header-text').text('Danh sách sinh viên trong lớp');
            loadStudentsByClass(classId);
        });
    }

    function displayStudentsByClass(data) {
        let rows = '';
        data.forEach((student, index) => {
            rows += `
                <tr>
                    <th scope="row">${index + 1}</th>
                    <td>${student.studentID}</td>
                    <td>${student.name}</td>
                    <td>${student.total_sessions}</td>
                    <td>${student.absences}</td>
                </tr>
            `;
        });
        $('#content-area').html(`
            <table class="table" style="width: 100%;">
                <thead class="thead-light">
                    <tr>
                        <th scope="col">STT</th>
                        <th scope="col">Mã sinh viên</th>
                        <th scope="col">Tên sinh viên</th>
                        <th scope="col">Số buổi học</th>
                        <th scope="col">Số buổi vắng</th>
                    </tr>
                </thead>
                <tbody id="students-table-body">
                    ${rows}
                </tbody>
            </table>
        `);
    }

    function filterSubjects(searchText) {
        let filteredSubjects = window.subjectsData.filter(subject =>
            subject.id.toLowerCase().includes(searchText) ||
            subject.name.toLowerCase().includes(searchText)
        );
        displaySubjects(filteredSubjects);
    }

    function filterClasses(searchText) {
        let filteredClasses = window.classesData.filter(cls =>
            cls.id.toLowerCase().includes(searchText) ||
            cls.subjectName.toLowerCase().includes(searchText) ||
            cls.name.toLowerCase().includes(searchText) ||
            cls.teacherName.toLowerCase().includes(searchText)
        );

        // Kiểm tra xem hiện tại đang hiển thị danh sách sinh viên của lớp hay không
        if ($('#header-text').text() === 'Danh sách các lớp trong môn học') {
            filteredClasses = classesDataBySubject.filter(cls =>
                cls.id.toLowerCase().includes(searchText) ||
                cls.subjectName.toLowerCase().includes(searchText) ||
                cls.name.toLowerCase().includes(searchText) ||
                cls.teacherName.toLowerCase().includes(searchText)
            );
            displayClassesBySubject(filteredClasses);
        } else {
            displayClasses(filteredClasses);
        }

    }

    function filterStudents(searchText) {
        // Kiểm tra xem hiện tại đang hiển thị danh sách sinh viên của lớp hay không
        if ($('#header-text').text() === 'Danh sách sinh viên trong lớp') {
            filteredStudents = studentsDataByClass.filter(student =>
                student.studentID.toLowerCase().includes(searchText) ||
                student.name.toLowerCase().includes(searchText)
            );
            displayStudentsByClass(filteredStudents);
        }
    }

    // Xử lý sự kiện quay lại hoặc tiến tới trong trình duyệt
    window.addEventListener('popstate', function (event) {
        if (event.state) {
            switch (event.state.page) {
                case 'subjects':
                    $('#header-text').text('Danh sách các môn học');
                    loadSubjects();
                    break;
                case 'classes':
                    $('#header-text').text('Danh sách các lớp');
                    loadClasses();
                    break;
                case 'classesBySubject':
                    let subjectId = localStorage.getItem('currentSubjectId');
                    $('#header-text').text('Danh sách các lớp trong môn học');
                    loadClassesBySubject(subjectId);
                    break;
                case 'studentsByClass':
                    let classId = localStorage.getItem('currentClassId');
                    $('#header-text').text('Danh sách sinh viên trong lớp');
                    loadStudentsByClass(classId);
                    break;
                default:
                    break;
            }
        }
    });

    // Tải lại trạng thái từ localStorage
    let currentPage = localStorage.getItem('currentPage');
    if (currentPage) {
        switch (currentPage) {
            case 'subjects':
                $('#header-text').text('Danh sách các môn học');
                loadSubjects();
                break;
            case 'classes':
                $('#header-text').text('Danh sách các lớp');
                loadClasses();
                break;
            case 'classesBySubject':
                let subjectId = localStorage.getItem('currentSubjectId');
                $('#header-text').text('Danh sách các lớp trong môn học');
                loadClassesBySubject(subjectId);
                break;
            case 'studentsByClass':
                let classId = localStorage.getItem('currentClassId');
                $('#header-text').text('Danh sách sinh viên trong lớp');
                loadStudentsByClass(classId);
                break;
            default:
                break;
        }
    }
});

function toggleSidebar() {
    document.body.classList.toggle('sidebar-hidden');
}