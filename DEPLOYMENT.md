# 🚀 Guide de déploiement Railway

Ce guide vous accompagne pas à pas pour déployer l'API Kàff GUI sur Railway **sans erreurs**.

---

## 📋 Prérequis

- [ ] Compte GitHub avec le repo `kaff-GUI-API` pushé
- [ ] Compte Railway (gratuit) : https://railway.app/
- [ ] Tous les fichiers de déploiement créés (✅ déjà fait)

---

## 🎯 Étape 1 : Créer le projet Railway

1. Aller sur https://railway.app/
2. Cliquer sur **"New Project"**
3. Sélectionner **"Deploy from GitHub repo"**
4. Autoriser Railway à accéder à votre GitHub
5. Sélectionner le repo **`kaff-GUI-API`**
6. Railway va détecter automatiquement que c'est un projet Python

---

## 🗄️ Étape 2 : Ajouter PostgreSQL

1. Dans votre projet Railway, cliquer sur **"+ New"**
2. Sélectionner **"Database"** → **"Add PostgreSQL"**
3. Railway va créer une base de données et générer automatiquement :
   - `DATABASE_URL` (connexion complète)
   - `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`

**✅ Avantage :** La variable `DATABASE_URL` est automatiquement injectée dans votre app !

---

## 🔐 Étape 3 : Configurer les variables d'environnement

Dans votre service API Railway, aller dans **"Variables"** et ajouter :

### Variables obligatoires

```bash
# Django
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=<générer-une-clé-secrète-forte>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=*.railway.app,kaffgui.up.railway.app
DJANGO_LOG_LEVEL=INFO

# Database (déjà configuré automatiquement par Railway)
# DATABASE_URL=${{Postgres.DATABASE_URL}}

# Security
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DATABASE_SSL_REQUIRE=True

# CORS (ajuster selon votre domaine frontend)
DJANGO_CORS_ALLOWED_ORIGINS=https://votre-app-mobile.com

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=15
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
JWT_ROTATE_REFRESH_TOKENS=True
JWT_BLACKLIST_AFTER_ROTATION=True

# Axes (anti-brute-force)
AXES_FAILURE_LIMIT=5
AXES_COOLOFF_TIME_MINUTES=5
AXES_LOCKOUT_PARAMETERS=ip_address,username

# Crypto (clés NaCl pour chiffrement des credentials)
APP_CRYPTO_PRIVATE_KEY=<générer-avec-script-ci-dessous>
APP_CRYPTO_PUBLIC_KEY=<générer-avec-script-ci-dessous>

# Locale
DJANGO_LANGUAGE_CODE=fr
DJANGO_TIME_ZONE=Africa/Dakar
```

### 🔑 Générer les clés secrètes

**Django SECRET_KEY :**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Clés NaCl (APP_CRYPTO_*) :**
```python
python -c "from nacl.public import PrivateKey; import base64; sk = PrivateKey.generate(); print('APP_CRYPTO_PRIVATE_KEY=' + base64.b64encode(bytes(sk)).decode()); print('APP_CRYPTO_PUBLIC_KEY=' + base64.b64encode(bytes(sk.public_key)).decode())"
```

---

## 🚀 Étape 4 : Déployer

1. Railway va automatiquement détecter les changements sur GitHub
2. Le build va démarrer automatiquement
3. Suivre les logs en temps réel dans l'onglet **"Deployments"**

**Phases du déploiement :**
1. ✅ **Build** : Installation des dépendances (`pip install -r requirements.txt`)
2. ✅ **Release** : Migrations + collectstatic (via `Procfile`)
3. ✅ **Deploy** : Démarrage de Gunicorn

---

## ✅ Étape 5 : Vérifier le déploiement

Une fois déployé, Railway vous donne une URL : `https://kaff-gui-api-production.up.railway.app`

**Tester les endpoints :**

```bash
# Health check
curl https://votre-app.railway.app/health/

# Swagger UI
https://votre-app.railway.app/api/docs/

# Admin Django
https://votre-app.railway.app/admin/
```

---

## 🔧 Étape 6 : Créer un super-utilisateur

Railway ne permet pas d'exécuter des commandes interactives directement. Utilisez cette approche :

**Option 1 : Via script Python (recommandé)**

Créer un fichier `scripts/create_superuser.py` :

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.users.models import User

if not User.objects.filter(email='admin@kaffgui.com').exists():
    User.objects.create_superuser(
        email='admin@kaffgui.com',
        password='ChangeMe123!',  # À changer immédiatement
        first_name='Admin',
        last_name='Kàff GUI'
    )
    print('✅ Superuser created')
else:
    print('ℹ️ Superuser already exists')
```

Puis dans Railway CLI ou via un déploiement temporaire :
```bash
python scripts/create_superuser.py
```

**Option 2 : Via Railway CLI**

```bash
# Installer Railway CLI
npm install -g @railway/cli

# Se connecter
railway login

# Lier le projet
railway link

# Exécuter la commande
railway run python manage.py createsuperuser
```

---

## 🎨 Étape 7 : Configurer un domaine personnalisé (optionnel)

1. Dans Railway, aller dans **"Settings"** → **"Domains"**
2. Cliquer sur **"Generate Domain"** pour un sous-domaine Railway gratuit
3. Ou ajouter votre propre domaine personnalisé

**Mettre à jour `DJANGO_ALLOWED_HOSTS` :**
```bash
DJANGO_ALLOWED_HOSTS=*.railway.app,votre-domaine.com
```

---

## 🐛 Dépannage

### Erreur : "Application failed to respond"

**Cause :** Gunicorn ne bind pas sur le bon port

**Solution :** Vérifier que `Procfile` utilise `$PORT` :
```
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

### Erreur : "ModuleNotFoundError"

**Cause :** Dépendance manquante dans `requirements.txt`

**Solution :** Vérifier que toutes les dépendances de `pyproject.toml` sont dans `requirements.txt`

### Erreur : "ALLOWED_HOSTS"

**Cause :** Le domaine Railway n'est pas dans `ALLOWED_HOSTS`

**Solution :** Ajouter `*.railway.app` dans la variable d'environnement :
```bash
DJANGO_ALLOWED_HOSTS=*.railway.app,localhost,127.0.0.1
```

### Erreur : "Database connection failed"

**Cause :** PostgreSQL pas lié ou `DATABASE_URL` incorrecte

**Solution :** 
1. Vérifier que PostgreSQL est bien ajouté au projet
2. Vérifier que `DATABASE_URL` est bien définie (Railway le fait automatiquement)
3. Vérifier `DATABASE_SSL_REQUIRE=True` en production

### Build timeout

**Cause :** Installation des dépendances trop longue

**Solution :** Railway a un timeout de 10 minutes, largement suffisant pour ce projet. Si ça timeout :
1. Vérifier que `requirements.txt` ne contient pas de dépendances dev inutiles
2. Utiliser `--no-cache-dir` dans le buildCommand si nécessaire

---

## 📊 Monitoring

Railway fournit automatiquement :
- **Logs en temps réel** : Onglet "Logs"
- **Métriques** : CPU, RAM, Network
- **Alertes** : Notifications en cas d'erreur

**Logs structurés JSON :**
Votre API utilise `structlog` qui génère des logs JSON en production, parfaits pour l'analyse.

---

## 💰 Coûts

**Plan gratuit Railway :**
- $5 de crédit/mois
- Suffisant pour :
  - 1 API Django (petit trafic)
  - 1 PostgreSQL (500 MB)
  - ~500 heures d'exécution/mois

**Plan Hobby ($5/mois) :**
- $5 de crédit + $5 supplémentaires
- Recommandé pour la production

---

## 🔄 Déploiement continu

Railway redéploie automatiquement à chaque push sur `main` :

```bash
git add .
git commit -m "feat: nouvelle fonctionnalité"
git push origin main
# Railway détecte le push et redéploie automatiquement
```

---

## ✅ Checklist finale

Avant de considérer le déploiement comme terminé :

- [ ] API accessible via l'URL Railway
- [ ] Health check répond : `/health/`
- [ ] Swagger UI accessible : `/api/docs/`
- [ ] Admin Django accessible : `/admin/`
- [ ] Superuser créé et connexion OK
- [ ] Logs structurés visibles dans Railway
- [ ] Variables d'environnement toutes configurées
- [ ] HTTPS actif (cadenas vert dans le navigateur)
- [ ] CORS configuré pour l'app mobile
- [ ] Tests de l'API depuis Postman/Swagger

---

## 🎉 Félicitations !

Votre API Kàff GUI est maintenant déployée en production sur Railway avec :
- ✅ HTTPS/TLS automatique
- ✅ PostgreSQL managé
- ✅ Déploiement continu
- ✅ Logs centralisés
- ✅ Sécurité OWASP complète

**URL de l'API :** `https://votre-app.railway.app`

**Prochaines étapes :**
1. Configurer l'app mobile pour pointer vers cette URL
2. Tester le flow complet d'inscription/connexion
3. Monitorer les logs et performances
4. Configurer un domaine personnalisé (optionnel)
