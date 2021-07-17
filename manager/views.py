from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
import datetime
import math

from .forms import *


def is_captain(user):
    return user.groups.filter(name='Captains').exists()

def time_plus(time, timedelta):
    start = datetime.datetime(
        2000, 1, 1,
        hour=time.hour, minute=time.minute, second=time.second)
    end = start + timedelta
    return end.time()

@login_required(login_url='login')
def erg_booking(request):
    if request.method == 'POST':
        f = BookErgForm(request.POST)
        booking = f.save(commit=False)

        if (booking.date<datetime.date.today()):
            return HttpResponse("Can't book on a past date")

        otherBookingsOnSameErg = ErgBooking.objects.filter(erg=booking.erg.id, date=booking.date)
        otherBookingsIMade = ErgBooking.objects.filter(person = request.user.id, date=booking.date)

        for otherBooking in otherBookingsOnSameErg | otherBookingsIMade:
            book1Start = booking.startTime
            book1End = time_plus(booking.startTime,datetime.timedelta(hours=booking.hours))

            book2Start = otherBooking.startTime
            book2End = time_plus(otherBooking.startTime,datetime.timedelta(hours=otherBooking.hours))
            if (book1Start>book2Start and book1End<book2End) or (book1Start<book2Start and book1End>book2Start) or (book1Start<book2End and book1End>book2End):
                return HttpResponse("Booking is overlapping")
        booking.person = request.user
        booking.save()

    dates = []
    today = datetime.date.today()
    for i in range(0, 7):
        dates.append(today + datetime.timedelta(days=i))

    bookingDays = [{'date': d, 'ergBookings': [{'erg': erg, 'form': BookErgForm({'startTime': datetime.time(7,0), 'hours': 1, 'erg': erg.id, 'date': d}), 'bookings': ErgBooking.objects.filter(erg = erg.id, date = d)} for erg in Erg.objects.all()]} for d in dates]

    context = {
        'userId': request.user.id,
        'bookingDays': bookingDays,
        'currentUserId': request.user.id
    }

    return render(request, 'erg_booking_manager.html', context)

@login_required(login_url='login')
def erg_manager_teams(request, team_id):
    if not is_captain(request.user):
        return render(request, 'no_permission.html', {})

    workoutProfiles =  [{'user': User.objects.get(id=it.person.id), 'workoutDatas': [workout_create_data(w) for w in ErgWorkout.objects.filter(person=it.person.id)]} for it in InTeam.objects.filter(team=team_id)]
    while(len(workoutProfiles)%3 is not 0):
        workoutProfiles.append({'isPadding': True})

    context = {
        'workoutProfiles': workoutProfiles,
        'teams': Team.objects.all(),
        'currentTeamId': team_id
    }

    return render(request, 'erg_manager.html', context)

@login_required(login_url='login')
def outing_manager_overview(request):
    if not is_captain(request.user):
        return render(request, 'no_permission.html', {})
    today = datetime.date.today()

    od = [{"outing": outing,
                        "rowerCount": InOuting.objects.filter(outing=outing.id).filter(type='RW').count(),
                        "coxCount": InOuting.objects.filter(outing=outing.id).filter(type='CX').count(),
                        "coachCount": InOuting.objects.filter(outing=outing.id).filter(type='CC').count(),
                        "rowerSignup": Available.objects.filter(outing=outing.id).filter(type='RW').count(),
                        "coxSignup": Available.objects.filter(outing=outing.id).filter(type='CX').count(),
                        "coachSignup": Available.objects.filter(outing=outing.id).filter(type='CC').count()} for outing
                       in Outing.objects.filter(date__gte=today)
                       ]

    context = {
        'outingData': sorted(od, key=lambda x: x["outing"].date)
    }

    return render(request, 'outing_manager_overview.html', context)


@login_required(login_url='login')
def create_workout(request):
    if request.method == 'POST':
        f = CreateErgWorkout(request.POST)

        if f.is_valid():
            w = f.save(commit=False)
            w.person = request.user
            w.save()
            return render(request, 'outing_created.html', {})

    form = CreateErgWorkout(initial={})

    context = {
        'form': form,
    }

    return render(request, 'create_erg_workout.html', context)


@login_required(login_url='login')
def create_outing(request):
    if not is_captain(request.user):
        return render(request, 'no_permission.html', {})

    if request.method == 'POST':
        f = CreateOutingForm(request.POST)
        f.save()
        post_data = dict(request.POST.lists())

        # Handles creating consecutive outings
        for i in range(1, int(post_data["repeat"][0])):
            ff = CreateOutingForm(request.POST)
            if ff.is_valid():
                o = ff.save()
                o.date += datetime.timedelta(days=i)
                o.save()
        return render(request, 'outing_created.html', {})
    else:
        form = CreateOutingForm(initial={})

        context = {
            'form': form,
        }

        return render(request, 'create_outing.html', context)


SIGNUP_TYPES = {"RW": "rower", "CX": "cox", "CC": "coach"}


@login_required(login_url='login')
def signoff_outing(request):
    if request.method == 'POST':
        form = SignupOutingForm(request.POST)
        if form.is_valid():
            Available.objects.filter(person=request.user.id).filter(outing=form.cleaned_data['outing'],
                                                                    type=form.cleaned_data['type']).delete()
            return HttpResponse("Success!")
        else:
            return HttpResponse("Error!")
    else:
        return None


@login_required(login_url='login')
def delete_erg_booking(request):
    # Todo: Actually use the form, for some demonic reason the cleaned data is empty atm
    if request.method == 'POST':
        form = DeleteWorkoutForm(request.POST)
        if form.is_valid():
            ErgBooking.objects.filter(person=request.user.id).filter(
                id=int(dict(request.POST.lists())['b_id'][0])).delete()
            return HttpResponse("Success!")
        else:
            return HttpResponse("Error!")
    else:
        return None


@login_required(login_url='login')
def delete_workout(request):
    # Todo: Actually use the form, for some demonic reason the cleaned data is empty atm
    if request.method == 'POST':
        form = DeleteWorkoutForm(request.POST)
        if form.is_valid():
            ErgWorkout.objects.filter(person=request.user.id).filter(
                id=int(dict(request.POST.lists())['w_id'][0])).delete()
            return HttpResponse("Success!")
        else:
            return HttpResponse("Error!")
    else:
        return None


@login_required(login_url='login')
def signup_outing(request):
    if request.method == 'POST':
        f = SignupOutingForm(request.POST)
        a = f.save(commit=False)
        if (Available.objects.filter(person=request.user.id).filter(outing=a.outing, type=a.type).count() > 0):
            return HttpResponse("You already signed up!")
        if (InTeam.objects.filter(person=request.user.id, team=a.outing.team.id).count() == 0):
            return HttpResponse("Not in team")
        a.person = request.user
        a.save()
        return HttpResponse("Success!")
    else:
        return None


@login_required(login_url='login')
def welcome(request):
    return render(request, 'welcome.html')


@login_required(login_url='login')
def my_profile(request):
    context = {
        'user': request.user,
        'teams': [it.team for it in InTeam.objects.filter(person=request.user.id)]
    }

    print(request.user.rowerprofile.crsid)

    return render(request, 'view_profile.html', context)


@login_required(login_url='login')
def my_outings(request):
    outings = [io.outing for io in InOuting.objects.filter(person=request.user.id)]

    today = datetime.date.today()

    context = {
        'outings': sorted(filter(lambda x: x.date >= today, outings), key=lambda x: x.date),
    }
    return render(request, 'view_outings.html', context)


def split(w):
    return (w.minutes * 60 + w.seconds + w.subSeconds * 0.1) / (w.distance / 500)

def workout_create_data(w):
    return {'workout': w, 'splitMin': math.floor(split(w) / 60), 'splitSec': math.floor(split(w) % 60),
     'splitSubSec': math.floor((split(w) * 10) % 10)}

@login_required(login_url='login')
def my_workouts(request):
    workouts = ErgWorkout.objects.filter(person=request.user.id)

    context = {
        'workoutData': [workout_create_data(w) for w in workouts],
    }
    return render(request, 'view_erg_workouts.html', context)


@login_required(login_url='login')
def outing_manager(request, outing_id):
    # Todo use forms

    if not is_captain(request.user):
        return render(request, 'no_permission.html', {})

    if request.method == 'POST':
        # Take a list of inouting pairs, and delete all others from the outing

        InOuting.objects.filter(outing=outing_id).delete()

        post_data = dict(request.POST.lists())
        av_ids = [a.person.id for a in Available.objects.filter(outing=outing_id)]
        o = Outing.objects.get(id=outing_id)
        print(post_data)
        # This is bad
        for key, value in post_data.items():
            if key.startswith("row_"):
                person = int(key[4:])
                print("PERSON IS " + str(person))
                if (person not in av_ids):
                    print("Cheeky")
                    return None
                io = InOuting(person=User.objects.get(id=person), type='RW', outing=o)
                io.save()
            else:
                if key == "status":
                    o.status = value[0]
                    o.save()
                if key == "cox":
                    if (int(value[0]) not in av_ids):
                        print("Cheeky")
                        print(int(value[0]))
                        return None
                    io = InOuting(person=User.objects.get(id=int(value[0])), type='CX', outing=o)
                    io.save()
                elif key == "coach":
                    if (int(value[0]) not in av_ids):
                        print("Cheeky")
                        print(int(value[0]))
                        return None
                    io = InOuting(person=User.objects.get(id=int(value[0])), type='CC', outing=o)
                    io.save()
    o = Outing.objects.get(id=outing_id)

    coxes = [x.person.id for x in InOuting.objects.filter(outing=outing_id).filter(type='CX')]
    coaches = [x.person.id for x in InOuting.objects.filter(outing=outing_id).filter(type='CC')]
    context = {
        'outing': o,
        'available_rowers': Available.objects.filter(outing=outing_id, type='RW'),
        'available_coxes': Available.objects.filter(outing=outing_id, type='CX'),
        'available_coaches': Available.objects.filter(outing=outing_id, type='CC'),
        'rowers': [x.person.id for x in InOuting.objects.filter(outing=outing_id).filter(type='RW')],
        'coxes': coxes,
        'coaches': coaches,
    }
    return render(request, 'outing_manager.html', context)


@login_required(login_url='login')
def signup_page(request, type):
    if type not in SIGNUP_TYPES.keys():
        return HttpResponse("Type doesn't exist!")

    today = datetime.date.today()
    if request.method == 'GET':
        context = {
            'outings': sorted(Outing.objects.filter(date__gte=today), key=lambda x: x.date),
            'availabilities': [x.outing.id for x in Available.objects.filter(person=request.user.id, type=type)],
            'type': type,
            'typeName': SIGNUP_TYPES[type]
        }
        return render(request, 'signup_sheet.html', context)
