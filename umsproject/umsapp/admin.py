from django.contrib import admin
from .models import (
    Department, Professor, Student, Course,
    Enrollment, Grade, Attendance, Announcement
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'created_at']
    search_fields = ['name', 'code']


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'get_full_name', 'department', 'designation']
    list_filter = ['department', 'designation']
    search_fields = ['user__first_name', 'user__last_name', 'employee_id']

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['roll_number', 'get_full_name', 'department', 'year', 'enrollment_date']
    list_filter = ['department', 'year']
    search_fields = ['user__first_name', 'user__last_name', 'roll_number']

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'professor', 'credits', 'semester']
    list_filter = ['department', 'semester']
    search_fields = ['name', 'code']


class GradeInline(admin.StackedInline):
    model = Grade
    extra = 0


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'enrolled_at']
    list_filter = ['status', 'course__department']
    search_fields = ['student__roll_number', 'student__user__first_name']
    inlines = [GradeInline]


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'marks_obtained', 'total_marks', 'grade']
    list_filter = ['grade']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'date', 'is_present']
    list_filter = ['is_present', 'course', 'date']
    date_hierarchy = 'date'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'course', 'created_at', 'is_active']
    list_filter = ['is_active', 'course']