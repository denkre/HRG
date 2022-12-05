from flask import Blueprint, render_template, request, g, send_file
from neo4j import GraphDatabase, basic_auth
from neo4j.exceptions import Neo4jError
import tempfile

app = Blueprint('pigeon_app', __name__, template_folder='templates')

driver = GraphDatabase.driver("bolt://127.0.0.1:7689", auth=basic_auth("neo4j", "knock-cape-reserve"))

def get_db():
    if 'db' not in g:
        g.neo4j_db = driver.session()

    return g.neo4j_db


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/add-pigeon', methods=['GET', 'POST'])
def add_pigeon():
    if request.method == "GET":
        return render_template("add_pigeon.html")
    else:
        cislo_krouzku_full = request.form.get("cislo_krouzku", "")
        if not cislo_krouzku_full:
            return render_template("add_pigeon.html", add_pigeon_success=False, error="Nebylo zadáno číslo kroužku! Data nebyla uložena")

        cislo_krouzku, rocnik = cislo_krouzku_full.split("/")

        holub_id = str(cislo_krouzku) + "-" + str(rocnik)

        # zkountrolovat zda holub id není v db

        holub_data = {
            "id" : holub_id,
            "cislo_krouzku": cislo_krouzku,
            "rocnik": rocnik,
            "pohlavi": request.form.get("pohlavi", ""),
            "plemeno": request.form.get("plemeno", ""),
            "barva": request.form.get("barva", ""),
            "kresba": request.form.get("kresba", ""),
            "chovatel": request.form.get("chovatel", ""),
            "bydliste": request.form.get("bydliste", ""),
            "exterierove_vady": request.form.get("exterierove_vady", ""),
            "exterierove_prednosti": request.form.get("exterierove_prednosti", ""),
            "cil_slechteni": request.form.get("cil_slechteni", ""),
            "povahove_vlastnosti": request.form.get("povahove_vlastnosti", ""),
        }

        try:
            db = get_db()
            db.run("CREATE (p:Pigeon $data )", data=holub_data)

            # check of matka
            # check if otec
            # check if matka in db
            # if not matka in db -> create matka
            # match holub, matka matka:Pigeon-[:MATKA]->holub:Pigeon
        except Neo4jError:
            return render_template("add_pigeon.html", add_pigeon_success=False, error="Data nebyla uložena.")

        return  render_template("add_pigeon.html", add_pigeon_success=True)


@app.route('/edit-pigeon/<pigeonID>', methods=['GET', 'POST'])
def edit_pigeon(pigeonID):
    if request.method == "POST":
        # pokud se změní pohlaví, rozvázat vztah s případnými potomky
        # pokud se změní matka či otec, rozvázat vztah s původním a přidat nový
        return "Zatím neimplementováno, změny nebyly uloženy.."
    else:
        db = get_db()
        q = "MATCH (a:Pigeon) " \
            "WHERE a.id = $id " \
            "RETURN a AS pigeon"
        result = db.run(q, id=pigeonID)
        data = result.data()[0]["pigeon"]
        # pridat do dat krouzky matky a otce
        return render_template("edit_pigeon.html", data=data)

@app.route('/delete-pigeon/<pigeonID>')
def delete_pigeon(pigeonID):
    return "Zatím neimplementováno"


@app.route('/pigeon-detail/<pigeonID>')
def pigeon_detail(pigeonID):
    db= get_db()
    q = "MATCH (a:Pigeon) "\
        "WHERE a.id = $id "\
        "RETURN a AS pigeon"
    result = db.run(q, id=pigeonID)
    data = result.data()[0]["pigeon"]
    return render_template("pigeon_detail.html", data=data)


@app.route("/my-pigeons")
def my_pigeons():
    db = get_db()
    q = "MATCH (a:Pigeon) " \
        "RETURN a AS pigeon"
    result = db.run(q)
    data = result.data()
    return render_template("pigeon_list.html", data=data)


# noinspection PyPep8Naming
@app.route('/pigeon-pedigree/<pigeonID>')
def pigeon_pedigree(pigeonID):
    return "Zatím neimplementováno"


@app.route('/pigeon-pedigree-download')
def pigeon_pedigree_download():
    # asi redirect
    return "Zatím neimplementováno"

@app.route('/test/rodokmen.pdf')
def test():
    tmp = tempfile.TemporaryFile()
    # tmp.write(b'some content')
    # tmp.seek(0)
    import pdf_gen_test
    output = pdf_gen_test.gen_test()
    output.write_stream(tmp)
    output.write(tmp)
    tmp.seek(0)
    return send_file(tmp, download_name="rodokmen.pdf")

