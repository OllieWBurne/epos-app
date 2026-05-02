import os
from flask import Flask, jsonify, request, render_template_string, redirect, session
from datetime import timedelta

app = Flask(__name__)

# ================= SECURITY =================
app.secret_key = os.environ.get("SECRET_KEY", "dev_fallback_key")
app.permanent_session_lifetime = timedelta(minutes=60)

def require_login():
    return session.get("logged_in", False)

# ================= STAFF =================
STAFF_PINS = {
    "1357": "Manager",
    "2468": "Staff"
}

# ================= MENU =================
items = {
    "Hot Food": {
        "Sausage Roll": 2.75,
        "Steak Slice": 3.75,
        "Cheese Slice": 3.75,
        "Bacon Cob": 3.50,
        "Sausage Cob": 3.50,
        "Sausage & Bacon Cob": 4.00,
        "Beef Burger": 4.75,
        "Cheeseburger": 5.25,
        "++Burger": 1.50,
        "++Cheese": 0.50,
    },
    "Cold": {"Cold Cob": 3.50},
    "Bakery": {"Pain Au Chocolat": 2.25},
    "Drinks": {
        "Rijo": 2.50,
        "Tea/Coffee": 2.00,
        "Water": 1.00
    }
}

state = {"cash": 0.0, "card": 0.0}

# ================= LOGIN =================
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<body style="background:#111;color:white;text-align:center;font-family:Arial;">
<h2>Staff Login</h2>
<form method="POST">
<input name="pin" type="password" placeholder="Enter PIN">
<br><br>
<button type="submit">Login</button>
</form>
</body>
</html>
"""

# ================= MAIN POS =================
POS_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;font-family:Arial;background:#111;color:white;}
.top{padding:10px;background:#1c1c1c;color:lightgreen;position:sticky;top:0;}

.container{display:flex;height:100vh;}

.left{width:25%;padding:10px;overflow:auto;background:#1a1a1a;}
.center{width:50%;padding:10px;display:flex;flex-direction:column;}
.right{width:25%;padding:10px;display:flex;flex-direction:column;}

.tabs{display:flex;flex-wrap:wrap;}
.tab{flex:1;margin:5px;padding:10px;background:#2ecc71;border:none;border-radius:10px;color:white;}

.items{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px;}

.item{background:#333;padding:18px;border-radius:10px;text-align:center;}

.noteGrid{display:grid;grid-template-columns:repeat(2,1fr);gap:5px;}

button{padding:12px;margin:5px 0;border:none;border-radius:10px;font-size:16px;}

.cash{background:#ff8c00;color:white;}
.card{background:#1e90ff;color:white;}
.exact{background:#87cefa;}
.undo{background:#444;color:white;}
.clear{background:#222;color:white;}
</style>
</head>

<body>

<div class="top" id="totals">TOTAL £0.00</div>

<div class="container">

<div class="left">
<h3>ORDER</h3>
<div id="order"></div>
<br>
<a href="/logout"><button class="clear">LOGOUT</button></a>
</div>

<div class="center">
<div id="tabs"></div>
<div class="items" id="items"></div>
</div>

<div class="right">

<h4>CASH</h4>
<div class="noteGrid" id="notes"></div>

<button class="cash" onclick="pay('cash')">CASH</button>
<button class="card" onclick="pay('card')">CARD</button>
<button class="exact" onclick="exact()">EXACT</button>
<button class="undo" onclick="undo()">UNDO</button>
<button class="clear" onclick="clearOrder()">CLEAR</button>

<br>
<button class="clear" onclick="resetDay()">END DAY</button>

</div>

</div>

<script>

let data = {{ items|tojson }};
let order=[], prices=[];
let total=0;
let cashTendered=0;

let notes=[50,20,10,5,2];
let current=Object.keys(data)[0];

function renderNotes(){
    let box=document.getElementById("notes");
    notes.forEach(v=>{
        let b=document.createElement("button");
        b.innerText="£"+v;
        b.onclick=()=>{cashTendered+=v; update();};
        box.appendChild(b);
    });
}

function renderTabs(){
    let t=document.getElementById("tabs");
    for(let c in data){
        let b=document.createElement("button");
        b.className="tab";
        b.innerText=c;
        b.onclick=()=>renderItems(c);
        t.appendChild(b);
    }
}

function renderItems(cat){
    let box=document.getElementById("items");
    box.innerHTML="";
    for(let n in data[cat]){
        let p=data[cat][n];
        let d=document.createElement("div");
        d.className="item";
        d.innerHTML=n+"<br>£"+p.toFixed(2);
        d.onclick=()=>add(n,p);
        box.appendChild(d);
    }
}

function add(n,p){
    order.push(n);
    prices.push(p);
    total+=p;
    update();
}

function undo(){
    if(order.length){
        total-=prices.pop();
        order.pop();
        update();
    }
}

function clearOrder(){
    order=[];prices=[];total=0;cashTendered=0;
    update();
}

function exact(){
    cashTendered=total;
    pay("cash");
}

function update(){
    let o={};
    order.forEach(i=>o[i]=(o[i]||0)+1);

    document.getElementById("order").innerHTML =
        Object.entries(o).map(([k,v])=>v+"x "+k).join("<br>");

    let change=Math.max(0,cashTendered-total);

    document.getElementById("totals").innerText =
        `TOTAL £${total.toFixed(2)} | CASH £${cashTendered.toFixed(2)} | CHANGE £${change.toFixed(2)}`;
}

function pay(method){
    fetch("/pay",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({total,method})
    }).then(()=>clearOrder());
}

function resetDay(){
    fetch("/reset",{method:"POST"});
}

renderTabs();
renderItems(current);
renderNotes();

</script>

</body>
</html>
"""

# ================= ROUTES =================
@app.route("/")
def index():
    if not require_login():
        return redirect("/login")
    return render_template_string(POS_HTML, items=items)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form.get("pin") in STAFF_PINS:
            session["logged_in"] = True
            session.permanent = True
            return redirect("/")
        return "Wrong PIN"
    return LOGIN_HTML

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/pay", methods=["POST"])
def pay():
    if not require_login():
        return "unauthorised", 403

    d=request.json
    if d["method"]=="cash":
        state["cash"]+=d["total"]
    else:
        state["card"]+=d["total"]
    return jsonify({"ok":True})

@app.route("/reset", methods=["POST"])
def reset():
    if not require_login():
        return "unauthorised", 403

    state["cash"]=0
    state["card"]=0
    return jsonify({"reset":True})

@app.route("/totals")
def totals():
    if not require_login():
        return "unauthorised", 403

    return jsonify({
        "cash":state["cash"],
        "card":state["card"],
        "total":state["cash"]+state["card"]
    })

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
