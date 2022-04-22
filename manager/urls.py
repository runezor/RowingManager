from django.urls import path
from django.conf.urls import include
from . import views

urlpatterns = [
    path('', views.welcome),
    path('createOuting/', views.create_outing),
    path('signupSheet/', views.signup_page),
    path('pastOutings/<str:crsid>', views.view_past_outings),
    path('signupSheet/signup/', views.signup_outing),
    path('signupSheet/signoff/', views.signoff_outing),
    path('deleteWorkout/', views.delete_workout),
    path('deleteErgBooking/', views.delete_erg_booking),
    path('createWorkout/', views.create_workout),
    path('myWorkouts/', views.my_workouts),
    path('ergManager/teams/<int:team_id>', views.erg_manager_teams),
    path('testEmailer/<str:crsid>', views.test_emailer),
    path('myOutings/', views.my_outings),
    path('myProfile/', views.my_profile),
    path('outings/<int:outing_id>/', views.outing_manager),
    path('outings/<int:outing_id>/addTeam/', views.outing_manager_add_team_availability),
    path('ergBooking/', views.erg_booking),
    path('outings/', views.outing_manager_overview),
    path('signup/', views.signup_user),
    path('signupBulk/', views.signup_users_bulk_view),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/profile/', views.welcome),
    path('viewCRSIDS/', views.view_crsids),
    path('analyse/<str:s>', views.outing_analyser),
    path('sendOutingReminderEmail/<int:outing_id>', views.outing_send_reminder_emails),
    path('sendOutingReminderEmail/<int:outing_id>/', views.outing_send_reminder_emails),
    path('deleteOuting/<int:outing_id>/', views.delete_outing),
    path('getRowerCSV/', views.get_rower_csv),
]
