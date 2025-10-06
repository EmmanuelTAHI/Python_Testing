import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, url_for


def loadClubs():
    with open("clubs.json") as c:
        listOfClubs = json.load(c)["clubs"]
        return listOfClubs


def loadCompetitions():
    with open("competitions.json") as comps:
        listOfCompetitions = json.load(comps)["competitions"]
        return listOfCompetitions


def loadBookings():
    try:
        with open("bookings.json") as bookings:
            listOfBookings = json.load(bookings)["bookings"]
            return listOfBookings
    except FileNotFoundError:
        return []


def saveBookings(bookings):
    with open("bookings.json", "w") as bookings_file:
        json.dump({"bookings": bookings}, bookings_file, indent=4)


def getClubBookingsForCompetition(club_name, competition_name):
    """Retourne le nombre total de places réservées par un club pour une compétition"""
    bookings = loadBookings()
    total_places = 0
    for booking in bookings:
        if booking["club"] == club_name and booking["competition"] == competition_name:
            total_places += booking["places"]
    return total_places


app = Flask(__name__)
app.secret_key = "something_special"

# Vider les réservations à chaque redémarrage du serveur
import os

if os.path.exists("bookings.json"):
    os.remove("bookings.json")

competitions = loadCompetitions()
clubs = loadClubs()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/showSummary", methods=["POST"])
def showSummary():
    email = request.form["email"]
    club = next((club for club in clubs if club["email"] == email), None)

    if not club:
        flash(
            "Adresse email non valide ou club introuvable. Veuillez vérifier votre email.",
            "error",
        )
        return render_template("index.html")

    return render_template(
        "welcome.html", club=club, competitions=competitions, datetime=datetime
    )


@app.route("/welcome/<club_name>")
def welcome(club_name):
    club = next((club for club in clubs if club["name"] == club_name), None)

    if not club:
        flash("Club introuvable. Veuillez vous reconnecter.", "error")
        return redirect(url_for("index"))

    return render_template(
        "welcome.html", club=club, competitions=competitions, datetime=datetime
    )


@app.route("/book/<competition>/<club>")
def book(competition, club):
    foundClub = [c for c in clubs if c["name"] == club][0]
    foundCompetition = [c for c in competitions if c["name"] == competition][0]

    if not foundClub or not foundCompetition:
        flash("Une erreur est survenue. Veuillez réessayer.", "error")
        return render_template("welcome.html", club=club, competitions=competitions)

    # verification de la date et de la comptétition
    competition_date = datetime.strptime(foundCompetition["date"], "%Y-%m-%d %H:%M:%S")
    if competition_date < datetime.now():
        flash(
            "Impossible de réserver : cette compétition est déjà passée ou en cours.",
            "warning",
        )
        return render_template(
            "welcome.html", club=foundClub, competitions=competitions, datetime=datetime
        )

    # Récupérer les réservations existantes du club pour cette compétition
    existing_bookings = getClubBookingsForCompetition(
        foundClub["name"], foundCompetition["name"]
    )

    return render_template(
        "booking.html",
        club=foundClub,
        competition=foundCompetition,
        existing_bookings=existing_bookings,
    )


@app.route("/purchasePlaces", methods=["POST"])
def purchasePlaces():
    competition = next(
        (c for c in competitions if c["name"] == request.form["competition"]), None
    )
    club = next((c for c in clubs if c["name"] == request.form["club"]), None)
    placesRequired = int(request.form["places"])

    if not competition or not club:
        flash("Compétition ou club introuvable. Veuillez réessayer.", "error")
        return redirect(url_for("index"))

    available_places = int(competition["numberOfPlaces"])
    club_points = int(club["points"])

    # Vérifier les réservations existantes du club pour cette compétition
    existing_bookings = getClubBookingsForCompetition(club["name"], competition["name"])
    total_club_bookings = existing_bookings + placesRequired

    # Vérifications logiques :
    if placesRequired > available_places:
        flash(
            f"Pas assez de places disponibles. Il ne reste que {available_places} place(s).",
            "warning",
        )
    elif placesRequired > 12:
        flash("Vous ne pouvez pas réserver plus de 12 places à la fois.", "warning")
    elif total_club_bookings > 12:
        remaining_allowed = 12 - existing_bookings
        if remaining_allowed <= 0:
            flash(
                f"Limite atteinte ! Vous avez déjà réservé {existing_bookings} places pour cette compétition. Maximum autorisé : 12 places par club.",
                "warning",
            )
        else:
            flash(
                f"Limite de réservation dépassée ! Vous avez déjà {existing_bookings} places. Vous ne pouvez réserver que {remaining_allowed} places supplémentaires (maximum 12 par club).",
                "warning",
            )
    elif placesRequired > club_points:
        flash(
            f"Pas assez de points dans votre compte. Vous avez {club_points} points disponibles.",
            "warning",
        )
    else:
        # Mise à jour des places et des points
        competition["numberOfPlaces"] = available_places - placesRequired
        club["points"] = club_points - placesRequired

        # Enregistrer la réservation
        bookings = loadBookings()
        new_booking = {
            "club": club["name"],
            "competition": competition["name"],
            "places": placesRequired,
            "timestamp": datetime.now().isoformat(),
        }
        bookings.append(new_booking)
        saveBookings(bookings)

        flash(
            f"Réservation réussie ! {placesRequired} places réservées pour {competition['name']}.",
            "success",
        )

    return render_template(
        "welcome.html", club=club, competitions=competitions, datetime=datetime
    )


# TODO: Add route for points display
@app.route("/displayPoints")
def displayPoints():
    """Route publique pour afficher le tableau des points - accessible sans authentification"""
    # Convertir les points en entiers pour le tri correct
    clubs_with_int_points = []
    for club in clubs:
        club_copy = club.copy()
        club_copy["points"] = int(club["points"])
        clubs_with_int_points.append(club_copy)

    return render_template("points.html", clubs=clubs_with_int_points)


@app.route("/logout")
def logout():
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
