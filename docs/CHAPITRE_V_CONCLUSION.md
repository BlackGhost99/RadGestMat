## Chapitre V — Conclusion

Objectif : synthétiser les travaux, rappeler les limites et proposer des perspectives d'évolution et recommandations opérationnelles.

Résumé
- Le projet RadGestMat propose une solution complète de gestion d'inventaire, d'attribution et de détection d'alertes adaptée au contexte hôtelier (ex : Radisson Blu). Les choix techniques retenus (Django, PostgreSQL, Celery, Redis, S3) visent la robustesse, l'observabilité et l'évolutivité.

Limites
- MVP visé : certaines fonctionnalités avancées (workflows multi-approbation, analyses prédictives) restent optionnelles et nécessitent itérations futures.
- Dépendances externes : configuration et coûts de services (S3, monitoring, mail) demandent arbitrage budgétaire.

Perspectives et évolutions futures
- Intégration d'un module de reporting avancé (KPIs consolidés, tendances historiques).
- Module mobile léger pour contrôles d'inventaire sur tablette/smartphone.
- Améliorations ML : prédiction de défaillance/mode de perte par analyse d'usage et remontées.

Recommandations opérationnelles
- Déployer d'abord sur staging et exécuter une campagne pilote avec le Service IT.
- Mettre en place un runbook de restauration et un plan de formation pour les agents.
- Mesurer KPIs initiaux : taux de retours à temps, nombre d'alertes critiques, taux de matériel endommagé.

Livrable attendu : synthèse 1–2 pages prête à présenter à la direction.
