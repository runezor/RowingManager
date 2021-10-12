from django.urls import path
from django.conf.urls import include
from . import views

urlpatterns = [
    path('', views.welcome),
    path('createOuting/', views.create_outing),
    path('signupSheet/<str:type>', views.signup_page),
    path('signupSheet/signup/', views.signup_outing),
    path('signupSheet/signoff/', views.signoff_outing),
    path('deleteWorkout/', views.delete_workout),
    path('deleteErgBooking/', views.delete_erg_booking),
    path('createWorkout/', views.create_workout),
    path('myWorkouts/', views.my_workouts),
    path('ergManager/teams/<int:team_id>', views.erg_manager_teams),
    path('myOutings/', views.my_outings),
    path('myProfile/', views.my_profile),
    path('outings/<int:outing_id>/', views.outing_manager),
    path('ergBooking/', views.erg_booking),
    path('outings/', views.outing_manager_overview),
    path('signupBulk/', views.signup_users_bulk_view),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/profile/', views.welcome),
]
