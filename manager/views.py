from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
import datetime
import math
import uuid
import re
import csv

from .emailer import sendSignupDetails, sendOutingReminders

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

        #Allows captains to book multiple
        if (is_captain(request.user)):
            otherBookingsIMade = ErgBooking.objects.none()

        for otherBooking in otherBookingsOnSameErg | otherBookingsIMade:
            book1Start = booking.startTime
            book1End = time_plus(booking.startTime,datetime.timedelta(hours=booking.hours))

            book2Start = otherBooking.startTime
            book2End = time_plus(otherBooking.startTime,datetime.timedelta(hours=otherBooking.hours))
            if (book1Start>=book2Start and book1End<book2End) or (book1Start<=book2Start and book1End>=book2Start) or (book1Start<book2End and book1End>book2End):
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
    while(len(workoutProfiles)%3 != 0):
        workoutProfiles.append({'isPadding': True})

    context = {
        'workoutProfiles': workoutProfiles,
        'teams': Team.objects.all(),
        'currentTeamId': team_id
    }

    return render(request, 'erg_manager.html', context)

@login_required(login_url='login')
def test_emailer(request, crsid):
    if not is_captain(request.user):
        return render(request, 'no_permission.html', {})
    sendSignupDetails(crsid, "123")
    return HttpResponse("Done")



@login_required(login_url='login')
def signup_user(request):
    if not is_captain(request.user):
        return render(request, 'no_permission.html', {})

    if request.method == 'POST':
        crsid = request.POST.get('crsid')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        team = request.POST.get('team')

        password = str(uuid.uuid4().hex.upper()[0:8])

        user = User.objects.create_user(username=crsid.lower(), email=crsid + "@cam.ac.uk", password=password)
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        teamNovice = InTeam.objects.create(person_id=user.id,
                                           team_id=Team.objects.get(name="Novices General").id)
        teamNovice.save()
        teamGeneral = InTeam.objects.create(person_id=user.id, team_id=Team.objects.get(name="General").id)
        teamGeneral.save()
        if (team == "men"):
            teamGeneral = InTeam.objects.create(person_id=user.id,
                                                team_id=Team.objects.get(name="Mens General").id)
            teamNovice2 = InTeam.objects.create(person_id=user.id,
                                                team_id=Team.objects.get(name="Mens Novices").id)
            teamGeneral.save()
            teamNovice2.save()

        if (team == "women"):
            teamGeneral = InTeam.objects.create(person_id=user.id,
                                                team_id=Team.objects.get(name="Womens General").id)
            teamNovice2 = InTeam.objects.create(person_id=user.id,
                                                team_id=Team.objects.get(name="Womens Novices").id)
            teamGeneral.save()
            teamNovice2.save()

        sendSignupDetails(crsid, password)
        return HttpResponse("Done!")

    return render(request, 'signup_user.html', {})

def signup_users_bulk(csv):
    #Uses format timestamp,name,crsid,draw,team,experience,...
    users = []
    for line in csv.splitlines():
        cleaned_line = re.sub('".*?"', "", line)
        vals = cleaned_line.split(",")
        if len(vals)>4:
            crsid = vals[2]
            names = vals[1].split(" ")
            firstname = names[0]
            lastname = names[1] if len(names)>1 else ""
            password = str(uuid.uuid4().hex.upper()[0:8])

            #signup user
            user=User.objects.create_user(username=crsid.lower(),email=crsid+"@cam.ac.uk",password=password)
            user.first_name = firstname
            user.last_name = lastname
            users.append({"object": user, "crsid": crsid, "password": password, "team": vals[4].lower()})
    for user in users:
        try:
            user["object"].save()

            #Consciseness? What's that?
            teamNovice = InTeam.objects.create(person_id = user["object"].id, team_id = Team.objects.get(name = "Novices General").id)
            teamNovice.save()
            teamGeneral = InTeam.objects.create(person_id = user["object"].id, team_id = Team.objects.get(name = "General").id)
            teamGeneral.save()
            if (user["team"]=="men"):
                teamGeneral = InTeam.objects.create(person_id = user["object"].id, team_id = Team.objects.get(name = "Mens General").id)
                teamNovice2 = InTeam.objects.create(person_id = user["object"].id, team_id = Team.objects.get(name = "Mens Novices").id)
                teamGeneral.save()
                teamNovice2.save()

            if (user["team"]=="women"):
                teamGeneral = InTeam.objects.create(person_id = user["object"].id, team_id = Team.objects.get(name = "Womens General").id)
                teamNovice2 = InTeam.objects.create(person_id = user["object"].id, team_id = Team.objects.get(name = "Womens Novices").id)
                teamGeneral.save()
                teamNovice2.save()

            sendSignupDetails(user["crsid"],user["password"])
        except:
            print(":)")

@login_required(login_url='login')
def signup_users_bulk_view(request):
    if not is_captain(request.user):
        return render(request, 'no_permission.html', {})

    if request.method == 'POST':
        f = SignupUsersBulkForm(request.POST)

        if f.is_valid():
            #todo: same issue as with delete form
            signup_users_bulk(request.POST.get('val'))

    return render(request, 'signup_users_bulk.html', {})

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
        'outingData': sorted(od, key=lambda x: (x["outing"].date, x["outing"].meetingTime))
    }

    return render(request, 'outing_manager_overview.html', context)



@login_required(login_url='login')
def outing_send_reminder_emails(request, outing_id):
    if request.method == 'POST':
        if not is_captain(request.user):
            return render(request, 'no_permission.html', {})

        sendOutingReminders(outing_id)

        return JsonResponse({'Hello':'There'})

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
        form = SignoffOutingForm(request.POST)
        if form.is_valid():
            if (InOuting.objects.filter(person=request.user.id,outing=form.cleaned_data['outing']).count()==0):
                Available.objects.filter(person=request.user.id).filter(outing=form.cleaned_data['outing'],
                                                                    type=form.cleaned_data['type']).delete()
                return HttpResponse("Success!")
            else:
                return HttpResponse("You're currently set to be in this outing. Please get in contact with your captain if you can't make it.")
        else:
            return HttpResponse("Error!")
    else:
        return None


@login_required(login_url='login')
def delete_outing(request, outing_id):
    if is_captain(request.user):
        outing = Outing.objects.get(id = outing_id)
        today = datetime.date.today()
        if outing.date>today:
            outing.delete()
            return HttpResponse("Success!")
        else:
            return HttpResponse("You can't delete active/past outings")
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
        #Only enforce team requirement if user is signing up as a rower
        if a.type=="RW" and (InTeam.objects.filter(person=request.user.id, team=a.outing.team.id).count() == 0):
            return HttpResponse("Not in team")
        a.person = request.user
        a.save()
        return HttpResponse("Success!")
    else:
        return None


@login_required(login_url='login')
def welcome(request):
    announcements = sorted([x for x in Announcement.objects.all() if ((not x.isTeamSpecific) or InTeam.objects.filter(person=request.user.id).filter(team=x.team.id).count()>0)], key = lambda a: a.priority, reverse=True)

    context = {
        'announcements': announcements,
    }

    return render(request, 'welcome.html', context)


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
        'outings': sorted(filter(lambda x: x.date >= today, outings), key=lambda x: (x.date, x.meetingTime)),
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
def view_crsids(request):

    if not is_captain(request.user):
        return render(request, 'no_permission.html', {})

    ret = ""
    for user in User.objects.all():
        ret += user.username+"@cam.ac.uk,"
    return HttpResponse(ret)

def outing_manager_context(outing_id):
    o = Outing.objects.get(id=outing_id)

    coxes = [x.person.id for x in InOuting.objects.filter(outing=outing_id).filter(type='CX')]
    coaches = [x.person.id for x in InOuting.objects.filter(outing=outing_id).filter(type='CC')]
    teams = [team for team in Team.objects.all()]

    available_rower_info = []
    for available_rower in Available.objects.filter(outing=outing_id, type='RW'):
        available_rower_info.append({"rower": available_rower})

    return {
        'outing': o,
        'available_rowers': Available.objects.filter(outing=outing_id, type='RW'),
        'available_coxes': Available.objects.filter(outing=outing_id, type='CX'),
        'available_coaches': Available.objects.filter(outing=outing_id, type='CC'),
        'all_users': User.objects.all(),
        'rowers': [x.person.id for x in InOuting.objects.filter(outing=outing_id).filter(type='RW')],
        'coxes': coxes,
        'coaches': coaches,
        'teams': teams
    }


@login_required(login_url='login')
def outing_manager_add_team_availability(request, outing_id):
    if not is_captain(request.user):
        return render(request, 'no_permission.html', {})

    av_ids = [a.person.id for a in Available.objects.filter(outing=outing_id)]

    if request.method == 'POST':
        teamId = request.POST.get('team')
        for inTeam in InTeam.objects.filter(team = teamId):
            if inTeam.person.id not in av_ids:
                #Add person to availabilities
                av = Available(person = inTeam.person, outing = Outing.objects.get(id=outing_id), type="RW", comment="")
                av.save()

    return render(request, 'outing_manager.html', outing_manager_context(outing_id))

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
                    io = InOuting(person=User.objects.get(id=int(value[0])), type='CX', outing=o)
                    io.save()
                elif key == "coach":
                    io = InOuting(person=User.objects.get(id=int(value[0])), type='CC', outing=o)
                    io.save()

    return render(request, 'outing_manager.html', outing_manager_context(outing_id))


@login_required(login_url='login')
def view_past_outings(request, crsid):
    if not is_captain(request.user):
        return render(request, 'no_permission.html', {})

    today = datetime.date.today()
    user = User.objects.get(username=crsid)
    if request.method == 'GET':
        context = {
            'in_outings': sorted(InOuting.objects.filter(person=user), key=lambda x: x.outing.date),
            'user': user
        }
        return render(request, 'view_past_outings.html', context)

@login_required(login_url='login')
def signup_page(request):
    today = datetime.date.today()
    if request.method == 'GET':
        context = {
            'outings': sorted(Outing.objects.filter(date__gte=today), key=lambda x: (x.date, x.meetingTime)),
            'teams': [{"isMember": InTeam.objects.filter(team = team.id, person=request.user.id).count()>0, "value": team } for team in Team.objects.all()],
            'availability_ids': [x.outing.id for x in Available.objects.filter(person=request.user.id)],
            'availability_rw_ids': [x.outing.id for x in Available.objects.filter(person=request.user.id, type='RW')],
            'availability_cx_ids': [x.outing.id for x in Available.objects.filter(person=request.user.id, type='CX')],
            'availability_cc_ids': [x.outing.id for x in Available.objects.filter(person=request.user.id, type='CC')],
            'comments': {x.outing.id: x.comment for x in Available.objects.filter(person=request.user.id)},
        }

        return render(request, 'signup_sheet.html', context)


@login_required(login_url='login')
def outing_analyser(request, s):
    # Todo use forms

    if not is_captain(request.user):
        return render(request, 'no_permission.html', {})

    outings_aug = []

    crsids = s.split(",")

    for o in Outing.objects.all():
        i = 0
        outing_names = []
        for io in InOuting.objects.filter(outing = o.id):
            if io.person.username in crsids:
                i += 1
                outing_names += [io.person.first_name + " " + io.person.last_name+ " ("+io.person.username+")"]
        outings_aug += [{"count": i, "outing": o, 'people_string': ",".join(outing_names)}]

    outings_aug = sorted(outings_aug, reverse=True, key=lambda x: x["count"])

    return render(request, 'outing_analyzer.html', {"outings_aug": outings_aug})

# For captains
def get_rower_csv(request):
    if not is_captain(request.user):
        return render(request, 'no_permission.html', {})

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="rowers.csv"'},
    )

    writer = csv.writer(response)
    cols = ['CRSID', 'First name', 'Last name']
    team_ids = []
    for team in Team.objects.all():
        cols += [team.name]
        team_ids += [team.id]

    writer.writerow(cols)
    for user in User.objects.all():
        row = [user.username, user.first_name, user.last_name]
        inTeams = [x.team.id for x in InTeam.objects.filter(person = user.id)]
        for team_id in team_ids:
            if team_id in inTeams:
                row += ["Yes"]
            else:
                row += ["No"]
        writer.writerow(row)

    return response