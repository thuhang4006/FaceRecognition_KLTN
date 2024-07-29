$(document).ready(function () {
    let studentsDataByClass = []; // Biến toàn cục để lưu dữ liệu sinh viên theo lớp

    $('#manage-classes').on('click', function (event) {
        event.preventDefault();
        $('#header-link').attr('href', '#');
        $('#header-text').text('Danh sách các lớp');
        loadClasses();
    });

    $('#manage-students').on('click', function (event) {
        event.preventDefault();
        $('#header-link').attr('href', '#');
        $('#header-text').text('Danh sách sinh viên');
        loadStudents();
    });

    $('#search-input').on('input', function () {
        let searchText = $(this).val().toLowerCase();
        if ($('#header-text').text() === 'Danh sách các lớp') {
            filterClasses(searchText);
        } else if ($('#header-text').text() === 'Danh sách sinh viên' || $('#header-text').text() === 'Danh sách sinh viên trong lớp') {
            filterStudents(searchText);
        }
    });

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
        fetch('/get_classes').then(response => response.json()).then(data => {
            window.classesData = data; // Lưu dữ liệu vào biến toàn cục để sử dụng cho tìm kiếm
            displayClasses(data);
        });
    }

    function loadStudents() {
        $('#content-area').html(`
            <table class="table" style="width: 100%;">
                <thead class="thead-light">
                    <tr>
                        <th scope="col">STT</th>
                        <th scope="col">Mã sinh viên</th>
                        <th scope="col">Tên sinh viên</th>
                        <th scope="col">Giới tính</th>
                        <th scope="col">Lớp</th>
                        <th scope="col">Dữ liệu</th>
                    </tr>
                </thead>
                <tbody id="students-table-body">
                </tbody>
            </table>
        `);
        fetch('/get_students').then(response => response.json()).then(data => {
            window.studentsData = data; // Lưu dữ liệu vào biến toàn cục để sử dụng cho tìm kiếm
            displayStudents(data);
        });
    }

    function loadStudentsByClass(classId) {
        fetch(`/get_students_by_class?class_id=${classId}`)
            .then(response => response.json())
            .then(data => {
                studentsDataByClass = data; // Lưu dữ liệu vào biến toàn cục
                displayStudentsByClass(data);
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
            $('#header-link').attr('href', '#');
            $('#header-text').text('Danh sách sinh viên trong lớp');
            loadStudentsByClass(classId);
        });
    }

    function displayStudents(data) {
        let rows = '';
        data.forEach((student, index) => {
            rows += `
                <tr>
                    <th scope="row">${index + 1}</th>
                    <td>${student.studentID}</td>
                    <td>${student.name}</td>
                    <td>${student.sex}</td>
                    <td>${student.className}</td>
                    <td>${student.facesData ? '✔' : '✖'}</td>
                </tr>
            `;
        });
        $('#students-table-body').html(rows);
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

    function filterClasses(searchText) {
        let filteredClasses = window.classesData.filter(cls =>
            cls.id.toLowerCase().includes(searchText) ||
            cls.subjectName.toLowerCase().includes(searchText) ||
            cls.name.toLowerCase().includes(searchText) ||
            cls.teacherName.toLowerCase().includes(searchText)
        );
        displayClasses(filteredClasses);
    }

    function filterStudents(searchText) {
        let filteredStudents = window.studentsData.filter(student =>
            student.studentID.toLowerCase().includes(searchText) ||
            student.name.toLowerCase().includes(searchText) ||
            student.sex.toLowerCase().includes(searchText) ||
            student.className.toLowerCase().includes(searchText)
        );

        // Kiểm tra xem hiện tại đang hiển thị danh sách sinh viên của lớp hay không
        if ($('#header-text').text() === 'Danh sách sinh viên trong lớp') {
            filteredStudents = studentsDataByClass.filter(student =>
                student.studentID.toLowerCase().includes(searchText) ||
                student.name.toLowerCase().includes(searchText)
            );
            displayStudentsByClass(filteredStudents);
        } else {
            displayStudents(filteredStudents);
        }
    }

    // Tải danh sách các lớp ban đầu
    loadClasses();

    function toggleSidebar() {
        document.body.classList.toggle('sidebar-hidden');
    }
});