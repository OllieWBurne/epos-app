from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

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

state = {
    "order": [],
    "prices": [],
    "total": 0.0,
    "cash": 0.0,
    "card": 0.0
}

notes = [50, 20, 10, 5, 2]

# ================= MAIN POS =================
HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EPOS</title>

<style>
body{
    margin:0;
    font-family:Arial;
    background:#111;
    color:white;
}

/* TOP BAR */
.top{
    padding:10px;
    background:#1c1c1c;
    font-size:18px;
    color:lightgreen;
    position:sticky;
    top:0;
    z-index:10;
}

/* LAYOUT */
.container{
    display:flex;
    height:100vh;
}

/* ORDER */
.left{
    width:25%;
    background:#1a1a1a;
    padding:10px;
    overflow:auto;
}

/* ITEMS (ALWAYS FIXED GRID) */
.center{
    width:50%;
    padding:10px;
    display:flex;
    flex-direction:column;
}

.tabs{
    display:flex;
    flex-wrap:wrap;
}

.tab{
    flex:1;
    min-width:100px;
    margin:5px;
    padding:10px;
    background:#2ecc71;
    color:white;
    border:none;
    border-radius:10px;
}

.items{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:10px;
    margin-top:10px;
    flex:1;
    overflow:hidden; /* IMPORTANT: keeps items ALWAYS visible */
}

.item{
    background:#333;
    padding:18px;
    border-radius:10px;
    text-align:center;
}

/* RIGHT PANEL */
.right{
    width:25%;
    padding:10px;
    display:flex;
    flex-direction:column;
}

/* CASH NOTES */
.noteGrid{
    display:grid;
    grid-template-columns:repeat(2,1fr);
    gap:5px;
    margin-bottom:10px;
}

.noteBtn{
    padding:10px;
    border:none;
    border-radius:10px;
    background:#444;
    color:white;
}

/* BUTTONS */
button{
    padding:12px;
    margin:5px 0;
    border:none;
    border-radius:10px;
    font-size:16px;
}

.cash{background:#ff8c00;color:white;}
.card{background:#1e90ff;color:white;}
.exact{background:#87cefa;}
.undo{background:#444;color:white;}
.clear{background:#222;color:white;}
</style>
</head>

<body>

<div class="top" id="totals">
TOTAL: £0.00 | CASH: £0.00 | CHANGE: £0.00
</div>

<div class="container">

<!-- ORDER -->
<div class="left">
<h3>ORDER</h3>
<div id="order"></div>
</div>

<!-- ITEMS -->
<div class="center">
<div id="tabs"></div>
<div class="items" id="items"></div>
</div>

<!-- CHECKOUT -->
<div class="right">

<h4>CASH NOTES</h4>
<div class="noteGrid" id="notes"></div>

<button class="cash" onclick="pay('cash')">CASH</button>
<button class="card" onclick="pay('card')">CARD</button>
<button class="exact" onclick="exact()">EXACT</button>
<button class="undo" onclick="undo()">UNDO</button>
<button class="clear" onclick="clearOrder()">CLEAR</button>

</div>

</div>

<script>

let data={{ items|tojson }};
let order=[], prices=[];
let total=0;
let cashTendered=0;

let current=Object.keys(data)[0];
let notes=[50,20,10,5,2];

function renderNotes(){
    let box=document.getElementById("notes");
    box.innerHTML="";
    notes.forEach(v=>{
        let b=document.createElement("button");
        b.className="noteBtn";
        b.innerText="£"+v;
        b.onclick=()=>addCash(v);
        box.appendChild(b);
    });
}

function addCash(v){
    cashTendered+=v;
    update();
}

function renderTabs(){
    let t=document.getElementById("tabs");
    t.innerHTML="";
    for(let c in data){
        let b=document.createElement("button");
        b.className="tab";
        b.innerText=c;
        b.onclick=()=>renderItems(c);
        t.appendChild(b);
    }
}

function renderItems(cat){
    current=cat;
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

    document.getElementById("order").innerHTML=
    Object.entries(o).map(([k,v])=>v+"x "+k).join("<br>");

    let change=Math.max(0,cashTendered-total);

    document.getElementById("totals").innerText=
    `TOTAL: £${total.toFixed(2)} | CASH: £${cashTendered.toFixed(2)} | CHANGE: £${change.toFixed(2)}`;
}

function pay(method){
    fetch("/pay",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({order,total,method,cashTendered})
    }).then(r=>r.json()).then(d=>{
        clearOrder();
    });
}

renderTabs();
renderItems(current);
renderNotes();

</script>

</body>
</html>
"""

# ================= API =================
@app.route("/")
def home():
    return render_template_string(HTML, items=items)

@app.route("/pay", methods=["POST"])
def pay():
    d=request.json

    if d["method"]=="cash":
        state["cash"]+=d["total"]
    else:
        state["card"]+=d["total"]

    return jsonify({"ok":True})

# ================= RUN =================
if __name__=="__main__":
    app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)
