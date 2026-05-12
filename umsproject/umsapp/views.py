from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from django.utils import timezone
from .models import (
    Department, Professor, Student, Course,
    Enrollment, Grade, Attendance, Announcement
)
from .forms import (
    LoginForm, StudentRegistrationForm, CourseForm,
    EnrollmentForm, GradeForm, AttendanceForm, AnnouncementForm,
    DepartmentForm,ProfessorRegistrationForm
)


# ─── Auth ────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# ─── Dashboard ───────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    user = request.user
    context = {
        'total_students': Student.objects.count(),
        'total_courses': Course.objects.count(),
        'total_departments': Department.objects.count(),
        'total_professors': Professor.objects.count(),
        'announcements': Announcement.objects.filter(is_active=True)[:5],
    }

    # Role-specific data
    if hasattr(user, 'student'):
        student = user.student
        enrollments = Enrollment.objects.filter(student=student, status='active').select_related('course')
        context['enrollments'] = enrollments
        context['role'] = 'student'
        context['student'] = student

    elif hasattr(user, 'professor'):
        professor = user.professor
        courses = Course.objects.filter(professor=professor)
        context['courses'] = courses
        context['role'] = 'professor'
        context['professor'] = professor

    elif user.is_staff:
        context['role'] = 'admin'
        context['recent_students'] = Student.objects.order_by('-enrollment_date')[:5]

    return render(request, 'dashboard.html', context)


# ─── Departments ─────────────────────────────────────────────────────────────

@login_required
def department_list(request):
    departments = Department.objects.annotate(
        student_count=Count('student'),
        course_count=Count('course')
    )
    return render(request, 'departments_list.html', {'departments': departments})


@login_required
def department_create(request):
    if not request.user.is_staff:
        messages.error(request, 'Permission denied.')
        return redirect('department_list')
    form = DepartmentForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Department created successfully.')
        return redirect('department_list')
    return render(request, 'form_generic.html', {'form': form, 'title': 'Add Department'})


# ─── Students ────────────────────────────────────────────────────────────────

@login_required
def student_list(request):
    query = request.GET.get('q', '')
    dept = request.GET.get('dept', '')
    students = Student.objects.select_related('user', 'department').all()
    if query:
        students = students.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(roll_number__icontains=query)
        )
    if dept:
        students = students.filter(department_id=dept)
    departments = Department.objects.all()
    return render(request, 'students_list.html', {
        'students': students, 'departments': departments,
        'query': query, 'selected_dept': dept
    })


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    enrollments = Enrollment.objects.filter(student=student).select_related('course', 'grade')
    return render(request, 'student_detail.html', {
        'student': student,
        'enrollments': enrollments,
    })


@login_required
def student_register(request):
    if not request.user.is_staff:
        messages.error(request, 'Permission denied.')
        return redirect('student_list')
    form = StudentRegistrationForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Student registered successfully.')
        return redirect('student_list')
    return render(request, 'form_generic.html', {'form': form, 'title': 'Register Student'})


# ─── Courses ─────────────────────────────────────────────────────────────────

@login_required
def course_list(request):
    query = request.GET.get('q', '')
    courses = Course.objects.select_related('department', 'professor__user').all()
    if query:
        courses = courses.filter(
            Q(name__icontains=query) | Q(code__icontains=query)
        )
    return render(request, 'courses_list.html', {'courses': courses, 'query': query})


@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    enrollments = Enrollment.objects.filter(course=course).select_related('student__user')
    announcements = Announcement.objects.filter(course=course, is_active=True)

    # Check if current student is enrolled
    is_enrolled = False
    if hasattr(request.user, 'student'):
        is_enrolled = Enrollment.objects.filter(
            student=request.user.student, course=course
        ).exists()

    return render(request, 'course_detail.html', {
        'course': course,
        'enrollments': enrollments,
        'announcements': announcements,
        'is_enrolled': is_enrolled,
    })


@login_required
def course_create(request):
    if not (request.user.is_staff or hasattr(request.user, 'professor')):
        messages.error(request, 'Permission denied.')
        return redirect('course_list')
    form = CourseForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Course created successfully.')
        return redirect('course_list')
    return render(request, 'form_generic.html', {'form': form, 'title': 'Create Course'})


# ─── Enrollment ──────────────────────────────────────────────────────────────

@login_required
def enroll_course(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)

    if not hasattr(request.user, 'student'):
        messages.error(request, 'Only students can enroll.')
        return redirect('course_detail', pk=course_pk)

    student = request.user.student

    if course.is_full():
        messages.error(request, 'This course is full.')
        return redirect('course_detail', pk=course_pk)

    enrollment, created = Enrollment.objects.get_or_create(student=student, course=course)
    if created:
        messages.success(request, f'Successfully enrolled in {course.name}.')
    else:
        messages.info(request, 'You are already enrolled in this course.')

    return redirect('course_detail', pk=course_pk)


@login_required
def drop_course(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    if hasattr(request.user, 'student'):
        Enrollment.objects.filter(student=request.user.student, course=course).update(status='dropped')
        messages.success(request, f'Dropped {course.name}.')
    return redirect('dashboard')


# ─── Grades ──────────────────────────────────────────────────────────────────

@login_required
def grade_entry(request, enrollment_pk):
    enrollment = get_object_or_404(Enrollment, pk=enrollment_pk)

    # Only the course's professor or admin can enter grades
    if not request.user.is_staff:
        if not hasattr(request.user, 'professor') or \
           enrollment.course.professor != request.user.professor:
            messages.error(request, 'Permission denied.')
            return redirect('course_detail', pk=enrollment.course.pk)

    grade, _ = Grade.objects.get_or_create(enrollment=enrollment)
    form = GradeForm(request.POST or None, instance=grade)
    if form.is_valid():
        form.save()
        messages.success(request, 'Grade saved.')
        return redirect('course_detail', pk=enrollment.course.pk)
    return render(request, 'form_generic.html', {
        'form': form, 'enrollment': enrollment
    })


# ─── Attendance ──────────────────────────────────────────────────────────────

@login_required
def mark_attendance(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)

    if not request.user.is_staff:
        if not hasattr(request.user, 'professor') or course.professor != request.user.professor:
            messages.error(request, 'Permission denied.')
            return redirect('course_detail', pk=course_pk)

    enrollments = Enrollment.objects.filter(course=course, status='active').select_related('student__user')

    if request.method == 'POST':
        date = request.POST.get('date')
        for enrollment in enrollments:
            is_present = request.POST.get(f'student_{enrollment.student.pk}') == 'on'
            Attendance.objects.update_or_create(
                student=enrollment.student,
                course=course,
                date=date,
                defaults={'is_present': is_present}
            )
        messages.success(request, 'Attendance saved.')
        return redirect('course_detail', pk=course_pk)

    return render(request, 'attendance_mark.html', {
        'course': course,
        'enrollments': enrollments,
        'today': timezone.now().date(),
    })


# ─── Announcements ───────────────────────────────────────────────────────────

@login_required
def announcement_create(request):
    form = AnnouncementForm(request.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.author = request.user
        obj.save()
        messages.success(request, 'Announcement posted.')
        return redirect('dashboard')
    return render(request, 'form_generic.html', {
        'form': form, 'title': 'Post Announcement'
    })
@login_required
def professor_register(request):
    if not request.user.is_staff:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    form = ProfessorRegistrationForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Teacher registered successfully.')
        return redirect('professor_list')
    return render(request, 'form_generic.html', {'form': form, 'title': 'Register Teacher'})


@login_required
def professor_list(request):
    professors = Professor.objects.select_related('user', 'department').all()
    return render(request, 'professors_list.html', {'professors': professors})