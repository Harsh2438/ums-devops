from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.dashboard, name='dashboard'),


    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),

  
    path('students/', views.student_list, name='student_list'),
    path('students/register/', views.student_register, name='student_register'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),

    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_pk>/enroll/', views.enroll_course, name='enroll_course'),
    path('courses/<int:course_pk>/drop/', views.drop_course, name='drop_course'),
    path('courses/<int:course_pk>/attendance/', views.mark_attendance, name='mark_attendance'),

 
    path('grades/<int:enrollment_pk>/', views.grade_entry, name='grade_entry'),

  
    path('announcements/create/', views.announcement_create, name='announcement_create'),
    path('teachers/', views.professor_list, name='professor_list'),
    path('teachers/register/', views.professor_register, name='professor_register'),
]