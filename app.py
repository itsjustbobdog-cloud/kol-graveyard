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
        "Promoted 3 competitors in the same week. Loyalty? Never heard of it.",
        "Called a token 'the next Ethereum' during the paid promo. It's currently worth less than your dignity.",
        "Every 'gem' they found turned out to be a rock. A heavy rock. That sank to zero.",
        "Their investment thesis: 'They paid me.'",
        "Built a reputation on being 'early.' Really they were just first in line at the bank.",
        "Their thread quality: 100%. The projects' quality: -100%. Math checks out.",
        "Hasn't met a token sale they didn't like. Your money? Not so much.",
        "Promised a thread 'tomorrow' for three weeks. The project rugged before they delivered.",
        "Shilled a gaming token. The game doesn't exist yet. Neither do the returns.",
        "Their 'research' consists of checking if the wire cleared.",
        "Every project they promote goes to the moon. Problem: It's the wrong moon.",
        "Has a sixth sense for scams. Unfortunately, it's the sense that tells them which ones to promote.",
    ],
    'long_roasts': {
        'extreme': [
            """{handle} enters the chat like they own the place. Spoiler: They don't own anything except {promo_count} bags of regret. 

Their playbook is simple: Find a dying project → Promise it's revolutionary → Pocket the check → Watch it crater → Repeat. 

{dead_count} projects have died on their watch. Not casualties. Victims. Each one sponsored, each one doomed from the moment they hit 'send tweet.'

They call it early. We call it paid. You call it whatever you want, but your wallet calls it 'ouch.'

The blockchain remembers. The graveyard grows. And {handle}? Still shilling. Still pretending. Still cashing checks while their followers hold the bags.""",

            """Meet {handle}: Web3's most prolific project mortician. They don't just kill projects—they bury them with receipts.

Their career by the numbers: {promo_count} paid promotions. {dead_count} confirmed disasters. That's a success rate that would get you fired from anywhere except influencer marketing.

Every thread starts the same: 'I don't usually do this, but...' Every thread ends the same: Project dead, followers rekt, handle richer. The cycle continues.

They called themselves researchers. Analysts. Early adopters. Reality check: They're salespeople. The worst kind—ones who sell products that don't exist to people who can't afford to lose.

The graveyard has a special place for {handle}. Front row. Center stone. Carved with every project name they helped kill. Rest in pieces, credibility. You died for a $5k retweet.""",

            """{handle} didn't just shill projects. They built a career on the corpses of dead tokens. 

Look at the timeline. {promo_count} promotional threads. Each one carefully crafted to sound authentic while being anything but. The language is always the same—'game-changer,' 'undervalued,' 'sleeping giant.' The projects? Always the same too—dead within months.

{dead_count} disasters later, what's changed? Nothing. They're still posting. Still promising. Still taking money to promote anything with a pulse and a marketing budget.

The worst part isn't that they shill. It's that they act surprised. 'How could I have known?' they say. We could have known. We did know. Anyone with two brain cells and a wallet they wanted to keep could see these were destined for zero.

But {handle} kept posting. Kept promoting. Kept collecting checks while their followers collected bags of worthless tokens.

Welcome to the graveyard, {handle}. Your tombstone is already here—we've been waiting for you to notice.""",
        ],
        'high': [
            """{handle} treats social media like a classifieds section. {promo_count} ads disguised as opinions. {dead_count} projects that didn't survive the spotlight.

They've mastered the art of looking authentic while being anything but. Every thread carefully calibrated. Every 'just my thoughts' actually a sales pitch with a human face.

The pattern is clear: Shill → Get paid → Watch it die → Shill again. No pause for reflection. No learning from mistakes. Just another check, another project, another set of followers left holding worthless tokens.

Respect the hustle? Hard to respect something that leaves this many victims.""",

            """{handle}'s timeline reads like a graveyard tour guide. 'Over here we have Project X, rugged in March. Over there, Token Y, died in April.'

{promo_count} promotions. {dead_count} disasters. At what point does 'bad luck' become 'bad judgment'? At what point do we stop calling them an influencer and start calling them a warning?

The answer: Right now. Welcome to your final resting place.""",
        ],
        'medium': [
            """{handle} walks the line between 'influencer' and 'infomercial host.' {promo_count} promotions, {dead_count} casualties. 

Not the worst we've seen. Not the best either. They disclose sometimes, hide it others. The result is a timeline that looks like an ad break with occasional personality.

Is it malicious? Probably not. Is it helpful to anyone following their 'recommendations'? Also probably not. 

Bury them, but make it quick. They've got another sponsored thread to post.""",
        ],
        'low': [
            """{handle} barely qualifies for the graveyard. {promo_count} promotions—barely a blip on the radar. {dead_count} disasters—statistically insignificant.

Are they perfect? No. Have they taken money to promote things? Yes. But compared to the monsters in this graveyard? {handle} is practically a saint.

Still here, though. Still buried. Still guilty of being just shilly enough to notice, just subtle enough to think they got away with it.

They didn't.""",
        ],
    },
    'final_words': [
        "Here lies {handle}. Believer in too many 'revolutionary' projects.",
        "Rest in pieces, {handle}'s credibility.",
        "Gone but not forgotten. Mainly because the blockchain is eternal.",
        "They came, they shilled, they exited.",
        "Paid promotions don't lie. {handle} does.",
        "In memes we trust. In paid promos? Not so much.",
        "{handle}: Early to the pump, late to the dump.",
        "Here rests {handle}'s integrity. Died for engagement.",
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handle TEXT NOT NULL,
            evidence_type TEXT NOT NULL,
            evidence_text TEXT,
            evidence_url TEXT,
            innocence_claim TEXT,
            roast_escalation INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (handle) REFERENCES roasts(handle)
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
    
    # Get long roast based on level
    long_roast_template = random.choice(ROAST_TEMPLATES['long_roasts'].get(level, ROAST_TEMPLATES['long_roasts']['medium']))
    
    # Format the long roast
    main_roast = long_roast_template.format(
        handle=f"@{handle}",
        promo_count=promo_count,
        dead_count=dead_count,
        alive_count=alive_count,
        frequency=frequency
    )
    
    # Traditional short roast for tombstone display
    short_templates = ROAST_TEMPLATES['shill_level'].get(level, ROAST_TEMPLATES['shill_level']['medium'])
    short_roast = random.choice(short_templates).format(
        handle=f"@{handle}",
        promo_count=promo_count,
        dead_count=dead_count,
        alive_count=alive_count,
        frequency=frequency
    )
    
    # Get 5 specific insults
    insult_pool = ROAST_TEMPLATES['specific_insults'].copy()
    random.shuffle(insult_pool)
    selected_insults = insult_pool[:5]
    
    # Format them with handle
    formatted_insults = []
    for insult in selected_insults:
        formatted_insult = insult.replace('{handle}', f"@{handle}")
        formatted_insult = formatted_insult.replace('{promo_count}', str(promo_count))
        formatted_insult = formatted_insult.replace('{dead_count}', str(dead_count))
        formatted_insults.append(formatted_insult)
    
    # Multiple epitaphs for variety
    epitaphs = random.sample(ROAST_TEMPLATES['final_words'], min(3, len(ROAST_TEMPLATES['final_words'])))
    formatted_epitaphs = [e.format(handle=f"@{handle}") for e in epitaphs]
    
    return {
        'main_roast': main_roast,  # The long savage roast
        'short_roast': short_roast,  # For tombstone display
        'specific_insults': formatted_insults,
        'epitaphs': formatted_epitaphs,
        'shill_level': level,
        'promo_count': promo_count,
        'dead_count': dead_count,
        'follower_count': follower_count,
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
    
    # Combine both roasts and all data into one JSON structure
    full_roast_data = {
        'main_roast': roast_data.get('main_roast', ''),
        'short_roast': roast_data.get('short_roast', ''),
        'specific_insults': roast_data.get('specific_insults', []),
        'epitaphs': roast_data.get('epitaphs', []),
        'shill_level': roast_data.get('shill_level', 'medium')
    }
    
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
            json.dumps(full_roast_data),
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

@app.route('/submit-evidence', methods=['GET', 'POST'])
def submit_evidence():
    """Submit 'proof of innocence' - which we flip into worse roasts"""
    if request.method == 'POST':
        handle = request.form.get('handle', '').strip().lstrip('@')
        evidence_type = request.form.get('evidence_type', '')
        evidence_text = request.form.get('evidence_text', '')
        evidence_url = request.form.get('evidence_url', '')
        innocence_claim = request.form.get('innocence_claim', '')
        
        if not handle:
            return jsonify({'error': 'Need a handle to roast harder'}), 400
        
        # THE FLIP: Analyze their "innocence" and make it worse
        flip_result = analyze_evidence_and_flip(handle, evidence_type, evidence_text, innocence_claim)
        
        # Save the evidence
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO evidence (handle, evidence_type, evidence_text, evidence_url, innocence_claim, roast_escalation)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (handle.lower(), evidence_type, evidence_text, evidence_url, innocence_claim, flip_result['escalation_level']))
        conn.commit()
        conn.close()
        
        # Update the roast with the flipped analysis
        update_roast_with_flip(handle, flip_result)
        
        return render_template('evidence_result.html', 
                              handle=handle, 
                              flip=flip_result,
                              original_claim=innocence_claim)
    
    return render_template('submit_evidence.html')

def analyze_evidence_and_flip(handle, evidence_type, evidence_text, innocence_claim):
    """Analyze their 'proof of innocence' and weaponize it against them"""
    
    # More evidence = worse roast (the paradox)
    evidence_length = len(evidence_text) if evidence_text else 0
    evidence_word_count = len(evidence_text.split()) if evidence_text else 0
    
    # Calculate escalation based on how hard they tried
    escalation_level = 1
    if evidence_length > 500:
        escalation_level += 2  # Long defense = guilt
    if evidence_word_count > 100:
        escalation_level += 1  # Too many words = overcompensating
    if 'transparency' in innocence_claim.lower():
        escalation_level += 2  # Mentioning transparency = definitely hiding something
    if 'honest' in innocence_claim.lower():
        escalation_level += 1  # Claiming honesty = red flag
    if '#ad' in (evidence_text or ''):
        escalation_level += 3  # Used #ad in defense = self-own
    if 'not sponsored' in innocence_claim.lower():
        escalation_level += 2  # "Not sponsored" = definitely was
    if evidence_url:
        escalation_level += 1  # Linked proof = try-hard
    
    # Generate the flip based on evidence type
    flips = {
        'screenshots': {
            'title': '"Receipts" Backfired',
            'analysis': 'Shared screenshots as evidence. The timestamps reveal you posted the "unbiased review" 47 minutes after receiving the wire transfer.',
            'roast_addition': f'@{handle} tried to use screenshots as an alibi. Blockchain transactions don\'t lie, but you do.',
            'accusation': 'Receipts-based defense'
        },
        'statements': {
            'title': 'The "Trust Me Bro" Defense',
            'analysis': 'Provided a written statement claiming innocence. Studies show 93% of written defenses contain active lies. You\'re part of that 93%.',
            'roast_addition': f'@{handle} wrote a long post about integrity. Thesaurus abuse doesn\'t erase paid promotions.',
            'accusation': 'Word salad defense'
        },
        'transactions': {
            'title': 'Financial Transparency Trap',
            'analysis': 'Shared transaction records to prove "no payment." However, the receiving wallet is registered to a shell company in the Seychelles. Nice try.',
            'roast_addition': f'@{handle} showed us their "clean" books. Forgot about the offshore wallet. Amateur.',
            'accusation': 'Shell company enthusiast'
        },
        'contracts': {
            'title': 'Self-Incrimination Document',
            'analysis': 'Uploaded a contract to prove legitimacy. Page 4, Section 3: "Influencer agrees to promote token for 6 months." You played yourself.',
            'roast_addition': f'@{handle} uploaded the smoking gun. Contract? More like confession.',
            'accusation': 'Contractual shill'
        },
        'testimonials': {
            'title': 'Fake Friends, Real Promotion',
            'analysis': 'Submitted testimonials from "satisfied community members." All accounts created within the last 48 hours. All follow you first. All deleted after posting.',
            'roast_addition': f'@{handle}\'s testimonials came from burner accounts. The blockchain remembers, even when bots don\'t.',
            'accusation': 'Testimonial fraudster'
        }
    }
    
    flip_template = flips.get(evidence_type, {
        'title': 'Generic Guilt Confirmed',
        'analysis': 'Submitted evidence of "innocence." In 100% of cases, this level of defensive posting correlates with hidden paid promotions.',
        'roast_addition': f'@{handle} tried to prove innocence. The effort itself is the crime.',
        'accusation': 'Over-defensive suspect'
    })
    
    # Calculate collateral damage score
    collateral_roasts = [
        f"@{handle} brought receipts. Unfortunately, they're all from the store you were paid to promote.",
        f"@{handle}\'s defense strategy: Distract with volume, hope nobody reads.",
        f"@{handle} tried to clear their name. Added 3 more counts of suspicious behavior instead.",
        f"@{handle}: 'I have proof!' The proof: Screenshots with your own tweets cropped out.",
        f"@{handle}\'s innocence plea had more holes than the projects they promoted.",
        f"@{handle} built a case for innocence. The jury (us) finds you guilty of trying too hard.",
        f"@{handle}\'s evidence binder is thick. Almost as thick as the check they cashed.",
        f"@{handle} said 'check the receipts.' We did. You\'re on sale for $0.99 and clearance.",
    ]
    
    selected_collateral = random.sample(collateral_roasts, min(escalation_level, len(collateral_roasts)))
    
    return {
        'escalation_level': escalation_level,
        'flip_title': flip_template['title'],
        'flip_analysis': flip_template['analysis'],
        'roast_addition': flip_template['roast_addition'],
        'accusation': flip_template['accusation'],
        'collateral_roasts': selected_collateral,
        'innocence_score': max(0, 100 - (escalation_level * 20)),  # 100 = innocent, 0 = confirmed shill
        'verdict': 'GUILTY OF TRYING TOO HARD' if escalation_level > 2 else 'SUSPICIOUSLY DEFENSIVE',
        'conclusion': f"Your 'evidence' added {escalation_level} new charges to your record."
    }

def update_roast_with_flip(handle, flip_result):
    """Update existing roast with the flipped evidence analysis"""
    conn = get_db()
    c = conn.cursor()
    
    # Get current roast
    c.execute('SELECT * FROM roasts WHERE handle = ?', (handle.lower(),))
    row = c.fetchone()
    
    if row:
        roast = dict(row)
        current_text = roast['roast_text']
        current_insults = json.loads(roast['specific_insults']) if roast['specific_insults'] else []
        
        # Append the flip
        updated_text = f"{current_text}\n\n📎 EVIDENCE ANALYSIS:\n{flip_result['roast_addition']}"
        current_insults.extend(flip_result['collateral_roasts'])
        
        # Update
        c.execute('''
            UPDATE roasts 
            SET roast_text = ?, specific_insults = ?, dead_count = dead_count + ?
            WHERE handle = ?
        ''', (updated_text, json.dumps(current_insults[:5]), flip_result['escalation_level'], handle.lower()))
        conn.commit()
    
    conn.close()

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
else:
    # Initialize for gunicorn/production
    try:
        init_db()
        print(f"✅ Database initialized at {DATABASE}")
    except Exception as e:
        print(f"❌ Database init error: {e}")