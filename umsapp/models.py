from django.db import models
from django.contrib.auth.models import User


class Department(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Professor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    employee_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20, blank=True)
    designation = models.CharField(max_length=100, default='Assistant Professor')
    joining_date = models.DateField()
    photo = models.ImageField(upload_to='professors/', blank=True, null=True)

    def __str__(self):
        return f"Prof. {self.user.get_full_name()} ({self.employee_id})"


class Student(models.Model):
    YEAR_CHOICES = [(1, '1st Year'), (2, '2nd Year'), (3, '3rd Year'), (4, '4th Year')]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    roll_number = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20, blank=True)
    year = models.IntegerField(choices=YEAR_CHOICES, default=1)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    enrollment_date = models.DateField(auto_now_add=True)
    photo = models.ImageField(upload_to='students/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.roll_number})"


class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    professor = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, blank=True)
    credits = models.IntegerField(default=3)
    description = models.TextField(blank=True)
    semester = models.CharField(max_length=20, default='Fall 2025')
    max_students = models.IntegerField(default=60)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    def enrolled_count(self):
        return self.enrollment_set.count()

    def is_full(self):
        return self.enrolled_count() >= self.max_students


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('dropped', 'Dropped'),
        ('completed', 'Completed'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} -> {self.course}"


class Grade(models.Model):
    GRADE_CHOICES = [
        ('A+', 'A+'), ('A', 'A'), ('A-', 'A-'),
        ('B+', 'B+'), ('B', 'B'), ('B-', 'B-'),
        ('C+', 'C+'), ('C', 'C'), ('C-', 'C-'),
        ('D', 'D'), ('F', 'F'),
    ]

    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE)
    marks_obtained = models.FloatField(default=0)
    total_marks = models.FloatField(default=100)
    grade = models.CharField(max_length=3, choices=GRADE_CHOICES, blank=True)
    remarks = models.TextField(blank=True)
    graded_at = models.DateTimeField(auto_now=True)

    def percentage(self):
        return round((self.marks_obtained / self.total_marks) * 100, 2)

    def __str__(self):
        return f"{self.enrollment} - {self.grade}"


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateField()
    is_present = models.BooleanField(default=True)

    class Meta:
        unique_together = ('student', 'course', 'date')

    def __str__(self):
        status = "Present" if self.is_present else "Absent"
        return f"{self.student} | {self.course} | {self.date} - {status}"


class Announcement(models.Model):
    title = models.CharField(max_length=300)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True,
                               help_text="Leave blank for university-wide announcement")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']