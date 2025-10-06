import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, url_for


def loadClubs():
    try:
        with open("clubs.json") as c:
            listOfClubs = json.load(c)["clubs"]
            return listOfClubs
    except FileNotFoundError:
        flash("Erreur: Fichier clubs.json introuvable.", "error")
        return []
    except json.JSONDecodeError:
        flash("Erreur: Fichier clubs.json corrompu.", "error")
        return []
    except KeyError:
        flash("Erreur: Structure invalide dans clubs.json.", "error")
        return []
    except Exception as e:
        flash(f"Erreur lors du chargement des clubs: {str(e)}", "error")
        return []


def loadCompetitions():
    try:
        with open("competitions.json") as comps:
            listOfCompetitions = json.load(comps)["competitions"]
            return listOfCompetitions
    except FileNotFoundError:
        flash("Erreur: Fichier competitions.json introuvable.", "error")
        return []
    except json.JSONDecodeError:
        flash("Erreur: Fichier competitions.json corrompu.", "error")
        return []
    except KeyError:
        flash("Erreur: Structure invalide dans competitions.json.", "error")
        return []
    except Exception as e:
        flash(f"Erreur lors du chargement des compétitions: {str(e)}", "error")
        return []


def loadBookings():
    try:
        with open("bookings.json") as bookings:
            listOfBookings = json.load(bookings)["bookings"]
            return listOfBookings
    except FileNotFoundError:
        return []


def saveBookings(bookings):
    try:
        with open("bookings.json", "w") as bookings_file:
            json.dump({"bookings": bookings}, bookings_file, indent=4)
    except Exception as e:
        flash(f"Erreur lors de la sauvegarde des réservations: {str(e)}", "error")
        raise


def getClubBookingsForCompetition(club_name, competition_name):
    """Retourne le nombre total de places réservées par un club pour une compétition"""
    bookings = loadBookings()
    total_places = 0
    for booking in bookings:
        try:
            if (
                booking.get("club") == club_name
                and booking.get("competition") == competition_name
                and isinstance(booking.get("places"), (int, str))
            ):

                # Validation des places
                places = booking["places"]
                if isinstance(places, str):
                    places = int(places)

                # Ignorer les valeurs négatives ou nulles
                if places > 0:
                    total_places += places
        except (ValueError, TypeError):
            # Ignorer les réservations avec des données invalides
            continue
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
    try:
        email = request.form.get("email", "").strip()
        if not email:
            flash("L'adresse email est requise.", "error")
            return render_template("index.html")

        # Validation basique de l'email
        if "@" not in email or "." not in email:
            flash("Format d'email invalide.", "error")
            return render_template("index.html")

        club = next((club for club in clubs if club["email"] == email), None)
    except Exception as e:
        flash("Erreur lors de la validation de l'email.", "error")
        return render_template("index.html")

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
    try:
        # Validation et recherche sécurisée
        club_list = [c for c in clubs if c["name"] == club]
        competition_list = [c for c in competitions if c["name"] == competition]

        if not club_list:
            flash(f"Club '{club}' introuvable.", "error")
            return redirect(url_for("index"))
        if not competition_list:
            flash(f"Compétition '{competition}' introuvable.", "error")
            return redirect(url_for("index"))

        foundClub = club_list[0]
        foundCompetition = competition_list[0]
    except Exception as e:
        flash("Erreur lors de la recherche des données.", "error")
        return redirect(url_for("index"))

    if not foundClub or not foundCompetition:
        flash("Une erreur est survenue. Veuillez réessayer.", "error")
        return render_template("welcome.html", club=club, competitions=competitions)

    # verification de la date et de la comptétition
    try:
        competition_date = datetime.strptime(
            foundCompetition["date"], "%Y-%m-%d %H:%M:%S"
        )
        if competition_date < datetime.now():
            flash(
                "Impossible de réserver : cette compétition est déjà passée ou en cours.",
                "warning",
            )
            return render_template(
                "welcome.html",
                club=foundClub,
                competitions=competitions,
                datetime=datetime,
            )
    except ValueError:
        flash("Format de date invalide dans les données de compétition.", "error")
        return redirect(url_for("index"))

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
    try:
        # Validation des entrées
        competition_name = request.form.get("competition", "").strip()
        club_name = request.form.get("club", "").strip()
        places_str = request.form.get("places", "").strip()

        if not competition_name or not club_name or not places_str:
            flash("Tous les champs sont requis.", "error")
            return redirect(url_for("index"))

        # Validation du nombre de places
        try:
            placesRequired = int(places_str)
        except ValueError:
            flash("Le nombre de places doit être un nombre valide.", "error")
            return redirect(
                url_for("book", competition=competition_name, club=club_name)
            )

        if placesRequired <= 0:
            flash("Le nombre de places doit être positif.", "error")
            return redirect(
                url_for("book", competition=competition_name, club=club_name)
            )

        if placesRequired > 12:
            flash("Vous ne pouvez pas réserver plus de 12 places à la fois.", "error")
            return redirect(
                url_for("book", competition=competition_name, club=club_name)
            )

        # Recherche sécurisée
        competition = next(
            (c for c in competitions if c["name"] == competition_name), None
        )
        club = next((c for c in clubs if c["name"] == club_name), None)

    except Exception as e:
        flash("Erreur lors de la validation des données.", "error")
        return redirect(url_for("index"))

    if not competition or not club:
        flash("Compétition ou club introuvable. Veuillez réessayer.", "error")
        return redirect(url_for("index"))

    try:
        available_places = int(competition["numberOfPlaces"])
        club_points = int(club["points"])
    except (ValueError, TypeError):
        flash(
            "Erreur: Données invalides dans les informations du club ou de la compétition.",
            "error",
        )
        return redirect(url_for("index"))

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
        try:
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
        except Exception as e:
            flash("Erreur lors de l'enregistrement de la réservation.", "error")
            # Restaurer les valeurs originales en cas d'erreur
            competition["numberOfPlaces"] = available_places
            club["points"] = club_points

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
