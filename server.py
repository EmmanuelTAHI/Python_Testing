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


app = Flask(__name__)
app.secret_key = "something_special"

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
        flash("Erreur : adresse email non valide ou club introuvable.")
        return render_template("index.html")

    return render_template(
        "welcome.html", club=club, competitions=competitions, datetime=datetime
    )


@app.route("/welcome/<club_name>")
def welcome(club_name):
    """Route GET pour afficher la page welcome d'un club spécifique"""
    club = next((club for club in clubs if club["name"] == club_name), None)

    if not club:
        flash("Erreur : club introuvable.")
        return redirect(url_for("index"))

    return render_template(
        "welcome.html", club=club, competitions=competitions, datetime=datetime
    )


@app.route("/book/<competition>/<club>")
def book(competition, club):
    foundClub = [c for c in clubs if c["name"] == club][0]
    foundCompetition = [c for c in competitions if c["name"] == competition][0]

    if not foundClub or not foundCompetition:
        flash("Something went wrong-please try again")
        return render_template("welcome.html", club=club, competitions=competitions)

    # verification de la date et de la comptétition
    competition_date = datetime.strptime(foundCompetition["date"], "%Y-%m-%d %H:%M:%S")
    if competition_date < datetime.now():
        flash(
            "Erreur : vous ne pouvez pas réserver pour une compétition passée ou en cours."
        )
        return render_template(
            "welcome.html", club=foundClub, competitions=competitions, datetime=datetime
        )

    return render_template("booking.html", club=foundClub, competition=foundCompetition)


@app.route("/purchasePlaces", methods=["POST"])
def purchasePlaces():
    competition = next(
        (c for c in competitions if c["name"] == request.form["competition"]), None
    )
    club = next((c for c in clubs if c["name"] == request.form["club"]), None)
    placesRequired = int(request.form["places"])

    if not competition or not club:
        flash("Erreur: compétition ou club introuvable.")
        return redirect(url_for("index"))

    available_places = int(competition["numberOfPlaces"])
    club_points = int(club["points"])

    # Vérifications logiques :
    if placesRequired > available_places:
        flash("Erreur : pas assez de places disponibles.")
    elif placesRequired > 12:
        flash("Erreur : vous ne pouvez pas réserver plus de 12 places.")
    elif placesRequired > club_points:
        flash("Erreur : pas assez de points dans votre compte.")
    else:
        # Mise à jour des places et des points
        competition["numberOfPlaces"] = available_places - placesRequired
        club["points"] = club_points - placesRequired
        flash(f"Réservation réussie ! {placesRequired} places réservées.")

    return render_template(
        "welcome.html", club=club, competitions=competitions, datetime=datetime
    )


# TODO: Add route for points display
@app.route("/displayPoints")
def displayPoints():
    """Route publique pour afficher le tableau des points - accessible sans authentification"""
    return render_template("points.html", clubs=clubs)


@app.route("/logout")
def logout():
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
