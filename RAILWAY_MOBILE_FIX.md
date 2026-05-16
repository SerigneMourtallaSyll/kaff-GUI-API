# Fix CORS pour l'APK Mobile sur Railway

## Problème

L'APK mobile (EAS preview) ne peut pas se connecter à l'API Django sur Railway à cause de CORS.

**Symptôme :** En local ça marche, mais avec l'APK déployé, la connexion charge puis rien ne se passe.

**Cause :** Les apps mobiles natives (React Native) ne font pas de requêtes depuis une "origine" web classique. Django CORS bloque ces requêtes par défaut.

---

## Solution : Activer CORS pour toutes les origines

### Étape 1 : Ajouter la variable d'environnement sur Railway

1. Va sur le dashboard Railway : https://railway.app/
2. Sélectionne ton projet `kaff-GUI-API`
3. Onglet **Variables**
4. Clique sur **+ New Variable**
5. Ajoute :
   ```
   Nom : DJANGO_CORS_ALLOW_ALL_ORIGINS
   Valeur : True
   ```
6. Clique sur **Add** puis **Deploy**

### Étape 2 : Vérifier le déploiement

Attends que le déploiement se termine (1-2 minutes), puis teste :

```bash
# Test depuis ton terminal
curl -I https://web-production-c2c800.up.railway.app/api/v1/auth/public-key/
```

**Attendu :** Tu devrais voir dans les headers :
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Credentials: true
```

### Étape 3 : Tester avec l'APK

1. Ouvre l'APK sur ton téléphone
2. Essaie de te connecter
3. Ça devrait maintenant fonctionner !

---

## Alternative : Liste blanche d'origines (plus sécurisé)

Si tu veux être plus restrictif, tu peux autoriser seulement certaines origines :

```bash
# Sur Railway, au lieu de DJANGO_CORS_ALLOW_ALL_ORIGINS=True
DJANGO_CORS_ALLOWED_ORIGINS=https://ton-domaine.com,https://autre-domaine.com
```

**Mais attention :** Pour les apps mobiles natives, il n'y a pas vraiment d'"origine" à whitelister. `CORS_ALLOW_ALL_ORIGINS=True` est la solution standard pour les APIs mobiles.

---

## Sécurité

### Est-ce sécurisé d'autoriser toutes les origines ?

**Oui**, pour une API mobile avec authentification JWT :

1. ✅ **CORS ne protège pas l'API** — il protège le navigateur
2. ✅ **JWT protège l'API** — seuls les utilisateurs authentifiés peuvent accéder
3. ✅ **Rate limiting actif** — protection contre les abus (300 req/min)
4. ✅ **Brute-force protection** — django-axes (5 tentatives max)
5. ✅ **HTTPS obligatoire** — Railway force HTTPS automatiquement

### Qu'est-ce que CORS protège vraiment ?

CORS protège les **navigateurs web** contre les requêtes cross-origin malveillantes. 

**Pour les apps mobiles natives :**
- Pas de navigateur → CORS ne s'applique pas vraiment
- L'app contrôle directement les requêtes HTTP
- La sécurité vient de JWT + HTTPS + rate limiting

### Références

- [MDN : CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Django CORS Headers](https://github.com/adamchainz/django-cors-headers)
- [React Native + Django CORS](https://stackoverflow.com/questions/50732815/react-native-cors-issue)

---

## Vérification finale

Après avoir activé `DJANGO_CORS_ALLOW_ALL_ORIGINS=True` sur Railway :

### ✅ Checklist

- [ ] Variable ajoutée sur Railway
- [ ] Déploiement terminé (logs verts)
- [ ] `curl -I` montre `Access-Control-Allow-Origin: *`
- [ ] L'APK mobile peut se connecter
- [ ] Les logs Railway ne montrent pas d'erreurs CORS

### 🐛 Si ça ne marche toujours pas

1. **Vérifie les logs Railway** :
   ```
   Dashboard > Deployments > Logs
   ```
   Cherche : `CORS`, `OPTIONS`, `403`, `401`

2. **Vérifie les logs mobile** :
   ```bash
   adb logcat | grep -i "ReactNativeJS"
   ```
   Cherche : `Network Error`, `CORS`, `Failed to fetch`

3. **Teste l'API directement** :
   ```bash
   # Depuis ton téléphone (remplace par ton IP)
   curl https://web-production-c2c800.up.railway.app/api/v1/auth/public-key/
   ```

4. **Vérifie que l'URL est correcte** dans `.env` mobile :
   ```env
   EXPO_PUBLIC_API_BASE_URL=https://web-production-c2c800.up.railway.app/api/v1
   ```

---

## Commit et Push

Une fois que tu as vérifié que ça marche :

```bash
cd kaff-GUI-API
git add config/settings/base.py .env.example RAILWAY_MOBILE_FIX.md
git commit -m "fix: enable CORS for mobile app (React Native)"
git push origin main
```

Railway va automatiquement redéployer avec la nouvelle config.
