/**
 * Conventional Commits — cohérent avec le projet mobile Kàff-GUI-mobile.
 *
 * Types autorisés :
 *  feat     — nouvelle fonctionnalité
 *  fix      — correction de bug
 *  docs     — documentation uniquement
 *  style    — formatage, points-virgules manquants, etc.
 *  refactor — refacto sans changement fonctionnel ni de bug
 *  perf     — amélioration de performance
 *  test     — ajout / correction de tests
 *  chore    — tâches build, dépendances, tooling
 *  ci       — config CI
 *  build    — build system, dépendances externes
 *  revert   — annulation d'un commit antérieur
 */

module.exports = {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "body-max-line-length": [2, "always", 100],
    "subject-case": [
      2,
      "never",
      ["sentence-case", "start-case", "pascal-case", "upper-case"],
    ],
    "scope-enum": [
      2,
      "always",
      [
        "auth",
        "users",
        "pigeons",
        "cages",
        "couples",
        "reproductions",
        "sorties",
        "dashboard",
        "common",
        "config",
        "deps",
        "ci",
        "docs",
        "release",
      ],
    ],
  },
};
