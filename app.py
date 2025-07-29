from flask import Flask, request, render_template, redirect, url_for, flash
import datetime as time
import threading
import time as t
from lib.Blockchain import Blockchain

app = Flask(__name__)
app.secret_key = 'changeme'
blockchain = Blockchain()
auto_mint_enabled = False
AUTO_MINT_INTERVAL = 10
AUTO_MINT_MIN_TX = 1

# Rules for the auto mint
def auto_mint_worker():
    global auto_mint_enabled
    last_mint_time = t.time()
    while True:
        if auto_mint_enabled:
            now = t.time()
            tx_count = len(blockchain.pending_transactions)
            if tx_count >= AUTO_MINT_MIN_TX or (now - last_mint_time) >= AUTO_MINT_INTERVAL and tx_count > 0:
                if tx_count > 0:
                    result = blockchain.mine_pending_transactions()
                    if result:
                        blockchain.save_to_file()
                        flash("Bloc miné automatiquement.", "success")
                    last_mint_time = now
        t.sleep(5)


@app.context_processor
def inject_time():
    return {
    'current_time': time.time(),
    'auto_mint_enabled': auto_mint_enabled    
}
    

@app.route('/')
def index():
    return render_template("index.html", chain=blockchain.chain, transactions=blockchain.pending_transactions)

@app.route('/transactions/new', methods=['GET', 'POST'])
def new_transaction():
    if request.method == 'POST':
        sender = request.form.get('sender')
        recipient = request.form.get('recipient')
        amount = request.form.get('amount')

        if not sender or not recipient or not amount:
            flash("Tous les champs sont requis.", "error")
            return redirect(url_for('index'))

        try:
            blockchain.add_transaction(sender, recipient, float(amount))
            flash("Transaction ajoutée avec succès.", "success")
        except ValueError as e:
            flash(str(e), "error")

        return redirect(url_for('index'))

    return render_template("transaction.html")

@app.route('/mine', methods=['POST'])
def mine():
    result = blockchain.mine_pending_transactions()
    if result:
        blockchain.save_to_file()
        flash("Bloc miné avec succès.", "success")
    else:
        flash("Aucune transaction à miner.", "info")
    return redirect(url_for('index'))

@app.route('/validate', methods=['POST'])
def validate_chain():
    valid = blockchain.is_chain_valid()
    if valid:
        flash("La blockchain est valide.", "success")
    else:
        flash("La blockchain est invalide.", "error")
    return redirect(url_for('index'))

@app.route('/replace_chain', methods=['POST'])
def replace_chain():
    filename = request.form.get('filename')
    if not filename:
        flash("Nom de fichier requis.", "error")
        return redirect(url_for('index'))

    new_chain = blockchain.load_external_chain(filename)
    if not new_chain:
        flash("Fichier invalide ou introuvable.", "error")
        return redirect(url_for('index'))

    replaced = blockchain.replace_chain(new_chain)
    blockchain.save_to_file()
    if replaced:
        flash("Chaîne remplacée avec succès.", "success")
    else:
        flash("La chaîne existante est plus longue ou valide.", "info")
    return redirect(url_for('index'))

@app.route('/block/<int:index>')
def block_detail(index):
    if 0 <= index < len(blockchain.chain):
        block = blockchain.chain[index]
        return render_template("block_detail.html", block=block)
    else:
        flash("Bloc introuvable.", "error")
        return redirect(url_for('index'))
    
@app.route('/auto_mint', methods=['POST'])
def auto_mint():
    global auto_mint_enabled
    auto_mint_enabled = not auto_mint_enabled
    status = "activé" if auto_mint_enabled else "désactivé"
    flash(f"Minage automatique {status}.", "info")
    return redirect(url_for('index'))





if __name__ == '__main__':
    threading.Thread(target=auto_mint_worker, daemon=True).start()
    app.run(debug=True)
