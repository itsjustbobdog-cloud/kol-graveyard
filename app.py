"""
🪦 THE KOL GRAVEYARD 🪦
A web3 KOL roaster that exposes paid shills and puts them in the ground.
Built by Archon while Russ slept.
"""

import os
import re
import json
import sqlite3
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'graveyard-dev-key-change-in-production')

# Database path - Render needs absolute path
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'graveyard.db')
X_API_TOKEN = os.environ.get('X_API_BEARER_TOKEN')

# Shill detection patterns
SHILL_PATTERNS = [
    r'#ad\b',
    r'#sponsored\b',
    r'thanks? to .*?team',
    r'proud to announce.*partner',
    r'excited.*announce.*partner',
    r'partnered with',
    r'collaboration with',
    r'grateful.*opportunity',
    r'honored.*work with',
    r'thread.*why.*bullish',
    r'deep dive.*why.*project',
    r'gem.*dont miss',
    r'100x potential',
    r'moon imminent',
]

ROAST_TEMPLATES = {
    'shill_level': {
        'low': [
            "{handle} whispers about projects like they're sharing secrets. Barely a shill to be found.",
            "{handle} promotes occasionally, but mostly just vibes. Respectable.",
            "{handle} has standards. We found {promo_count} promos, but at least they're honest about it.",
        ],
        'medium': [
            "{handle} has shilled {promo_count} projects. {dead_count} are dead. The {alive_count} survivors are wondering why they hired this person.",
            "{handle} treats Twitter like a billboard. {promo_count} paid posts and counting. RIP authenticity.",
            "Found {promo_count} sponsored posts from {handle}. Disclosure game: weak. Shill game: strong.",
        ],
        'high': [
            "{handle} has promoted {promo_count} 'revolutionary' projects. {dead_count} have exit scammed. The other {alive_count} are ghost towns. Stay tuned.",
            "{handle}'s timeline is a graveyard of failed launches. {promo_count} promos, {dead_count} deaths. Coincidence?",
            "Alert: {handle} has shilled {promo_count} tokens. That's one every {frequency} days. Sleep? Unknown. Shame? Also unknown.",
            "{handle} doesn't sleep. They churn. {promo_count} paid promotions since they started. {dead_count} projects buried. The grind continues.",
        ],
        'extreme': [
            "{handle} has promoted {promo_count} projects. We stopped counting the dead ones at {dead_count}. Rest in peace to their credibility.",
            "Warning: {handle} is a professional hype machine. {promo_count} paid posts. Zero accountability. Full transparency: this person will promote literally anything.",
            "{handle} doesn't have followers. They have casualties. {promo_count} shills, {dead_count} disasters. The blockchain remembers.",
            "{handle} is the grim reaper of web3 projects. Touch their timeline, watch your bags die. {promo_count} victims and counting.",
        ],
    },
    'specific_insults': [
        "Promoted a project that rugged 3 days later. Not a record, but respectable.",
        "Called 5 coins 'undervalued gems' in one week. All down 90%+. Diamond hands? More like diamond bags.",
        "Posted #notfinancialadvice on a paid thread. The irony was not lost on us.",
        "Shilled a 'revolutionary' NFT project. The revolution lasted 48 hours.",
        "Claimed to be 'early' on a token they were paid to promote. Technical truth, moral gray area.",
        "Deleted the promo tweet after the project rugged. The blockchain doesn't forget, but they tried.",
        "Promised 'alpha' in paid threads. Delivered exit liquidity for founders instead.",
        "Shilled a DeFi project that got hacked. 'Bank-level security' they said. Bank-level robbery, more like.",
    ],
    'final_words': [
        "Here lies {handle}. Believer in too many 'revolutionary' projects.",
        "Rest in pieces, {handle}'s credibility.",
        "Gone but not forgotten. Mainly because the blockchain is eternal.",
        "They came, they shilled, they exited.",
        "Paid promotions don't lie. {handle} does.",
        "In memes we trust. In paid promos? Not so much.",
    ]
}

def init_db():
    """Initialize the graveyard database"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS roasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handle TEXT UNIQUE NOT NULL,
            display_name TEXT,
            follower_count INTEGER,
            promo_count INTEGER DEFAULT 0,
            dead_count INTEGER DEFAULT 0,
            roast_text TEXT NOT NULL,
            specific_insults TEXT,  -- JSON array
            death_date TEXT NOT NULL,  -- When they were added to graveyard
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_db():
    """Get database connection, initializing if needed"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    
    # Check if table exists, create if not (for Render ephemeral storage)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='roasts'")
    if not c.fetchone():
        c.execute('''
            CREATE TABLE roasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                handle TEXT UNIQUE NOT NULL,
                display_name TEXT,
                follower_count INTEGER,
                promo_count INTEGER DEFAULT 0,
                dead_count INTEGER DEFAULT 0,
                roast_text TEXT NOT NULL,
                specific_insults TEXT,
                death_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    
    return conn

def analyze_shill_level(promo_count):
    """Determine shill level based on promo frequency"""
    if promo_count == 0:
        return 'none'
    elif promo_count < 5:
        return 'low'
    elif promo_count < 15:
        return 'medium'
    elif promo_count < 30:
        return 'high'
    else:
        return 'extreme'

def generate_roast(handle, promo_count, dead_count, follower_count):
    """Generate a savage but fair roast"""
    level = analyze_shill_level(promo_count)
    alive_count = promo_count - dead_count
    
    # Calculate frequency
    if promo_count > 0:
        frequency = round(365 / promo_count) if promo_count < 365 else 1
    else:
        frequency = 0
    
    # Select main roast
    if level == 'none':
        main_roast = f"@{handle} appears to be clean. Either we're missing something, or they actually have integrity. Suspicious."
    else:
        templates = ROAST_TEMPLATES['shill_level'].get(level, ROAST_TEMPLATES['shill_level']['medium'])
        main_roast = random.choice(templates).format(
            handle=f"@{handle}",
            promo_count=promo_count,
            dead_count=dead_count,
            alive_count=alive_count,
            frequency=frequency
        )
    
    # Add specific insults
    num_insults = min(3, len(ROAST_TEMPLATES['specific_insults']))
    selected_insults = random.sample(ROAST_TEMPLATES['specific_insults'], num_insults)
    
    # Final words (epitaph)
    epitaph = random.choice(ROAST_TEMPLATES['final_words']).format(handle=f"@{handle}")
    
    return {
        'main_roast': main_roast,
        'specific_insults': selected_insults,
        'epitaph': epitaph,
        'shill_level': level,
        'promo_count': promo_count,
        'dead_count': dead_count,
        'follower_count': follower_count
    }

def mock_analyze_x_profile(handle):
    """
    Mock analysis of X profile for demo purposes.
    In production, this would call the X API.
    """
    # Deterministic but random-looking based on handle
    import hashlib
    hash_val = int(hashlib.md5(handle.encode()).hexdigest(), 16)
    
    # Generate pseudo-realistic stats
    promo_count = (hash_val % 50) + 1
    dead_count = int(promo_count * 0.4) + (hash_val % 10)
    follower_count = ((hash_val % 500) + 10) * 1000
    display_name = handle.title() if handle else "Unknown Shill"
    
    return {
        'handle': handle,
        'display_name': display_name,
        'follower_count': follower_count,
        'promo_count': promo_count,
        'dead_count': min(dead_count, promo_count),
        'recent_tweets': []
    }

def save_roast(handle, display_name, follower_count, promo_count, dead_count, roast_data):
    """Save roast to the graveyard database"""
    conn = get_db()
    c = conn.cursor()
    death_date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        c.execute('''
            INSERT OR REPLACE INTO roasts 
            (handle, display_name, follower_count, promo_count, dead_count, roast_text, specific_insults, death_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            handle.lower(),
            display_name,
            follower_count,
            promo_count,
            dead_count,
            roast_data['main_roast'],
            json.dumps(roast_data['specific_insults']),
            death_date
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving roast: {e}")
        return False
    finally:
        conn.close()

def get_graveyard_residents():
    """Get all roasts from the graveyard"""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT * FROM roasts 
        ORDER BY created_at DESC
    ''')
    residents = [dict(row) for row in c.fetchall()]
    conn.close()
    return residents

def get_roast_by_handle(handle):
    """Get specific roast from database"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM roasts WHERE handle = ?', (handle.lower(),))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

@app.route('/')
def index():
    """Homepage - The entrance to the graveyard"""
    return render_template('index.html')

@app.route('/roast', methods=['POST'])
def create_roast():
    """Create a new roast"""
    handle = request.form.get('handle', '').strip().lstrip('@')
    
    if not handle:
        return jsonify({'error': 'Need a handle to roast, chief.'}), 400
    
    # Check if already roasted
    existing = get_roast_by_handle(handle)
    if existing:
        return redirect(url_for('view_roast', handle=handle))
    
    # Analyze profile (mock for now)
    profile_data = mock_analyze_x_profile(handle)
    
    # Generate roast
    roast_data = generate_roast(
        handle=profile_data['handle'],
        promo_count=profile_data['promo_count'],
        dead_count=profile_data['dead_count'],
        follower_count=profile_data['follower_count']
    )
    
    # Save to graveyard
    save_roast(
        handle=handle,
        display_name=profile_data['display_name'],
        follower_count=profile_data['follower_count'],
        promo_count=profile_data['promo_count'],
        dead_count=profile_data['dead_count'],
        roast_data=roast_data
    )
    
    return redirect(url_for('view_roast', handle=handle))

@app.route('/r/<handle>')
def view_roast(handle):
    """View a specific roast"""
    handle = handle.lstrip('@').lower()
    roast = get_roast_by_handle(handle)
    
    if not roast:
        # Generate on the fly if not in database
        profile_data = mock_analyze_x_profile(handle)
        roast_data = generate_roast(
            handle=profile_data['handle'],
            promo_count=profile_data['promo_count'],
            dead_count=profile_data['dead_count'],
            follower_count=profile_data['follower_count']
        )
        
        save_roast(
            handle=handle,
            display_name=profile_data['display_name'],
            follower_count=profile_data['follower_count'],
            promo_count=profile_data['promo_count'],
            dead_count=profile_data['dead_count'],
            roast_data=roast_data
        )
        
        roast = get_roast_by_handle(handle)
    
    # Parse insults from JSON
    if isinstance(roast.get('specific_insults'), str):
        roast['specific_insults'] = json.loads(roast['specific_insults'])
    
    return render_template('roast.html', roast=roast)

@app.route('/graveyard')
def graveyard():
    """View the graveyard - all buried KOLs"""
    residents = get_graveyard_residents()
    
    # Parse insults for each
    for resident in residents:
        if isinstance(resident.get('specific_insults'), str):
            resident['specific_insults'] = json.loads(resident['specific_insults'])
    
    stats = {
        'total_buried': len(residents),
        'total_shills': sum(r['promo_count'] for r in residents),
        'total_casualties': sum(r['dead_count'] for r in residents)
    }
    
    return render_template('graveyard.html', residents=residents, stats=stats)

@app.route('/api/roast/<handle>')
def api_roast(handle):
    """API endpoint for programmatic access"""
    handle = handle.lstrip('@').lower()
    roast = get_roast_by_handle(handle)
    
    if not roast:
        return jsonify({'error': 'KOL not found. Try burying them first.'}), 404
    
    return jsonify({
        'handle': roast['handle'],
        'display_name': roast['display_name'],
        'roast': roast['roast_text'],
        'epitaph': roast.get('epitaph', ''),
        'promo_count': roast['promo_count'],
        'dead_count': roast['dead_count'],
        'death_date': roast['death_date']
    })

@app.route('/api/stats')
def api_stats():
    """API endpoint for graveyard stats"""
    residents = get_graveyard_residents()
    return jsonify({
        'total_buried': len(residents),
        'total_shills': sum(r['promo_count'] for r in residents),
        'total_casualties': sum(r['dead_count'] for r in residents),
        'average_shill_rate': sum(r['promo_count'] for r in residents) / len(residents) if residents else 0
    })

@app.route('/api/graveyard')
def api_graveyard():
    """API endpoint for all graveyard residents"""
    residents = get_graveyard_residents()
    for resident in residents:
        if isinstance(resident.get('specific_insults'), str):
            resident['specific_insults'] = json.loads(resident['specific_insults'])
    return jsonify(residents)

@app.route('/health')
def health_check():
    """Health check for Render"""
    try:
        conn = get_db()
        conn.execute('SELECT 1')
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))