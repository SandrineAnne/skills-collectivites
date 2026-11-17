# Dialogue pendant l'entretien

Mêmes principes que la fabrique (`dialogue-agent.md`) : le métier se demande, le technique se décide ; une question à la fois ; chaque question dit pourquoi ; « je ne sais pas » est accepté ; aucun sigle sans explication ; aucun refus sans solution. S'y ajoutent les règles propres à un moment où quelque chose ne marche pas.

## Le ton d'un dépannage

- **Rassurer et annoncer la méthode** dès le premier message : « On va d'abord remettre l'outil en marche, ensuite comprendre ce qui s'est passé. Je vous pose une question à la fois. »
- **Dire ce que l'on fait**, au fur et à mesure : « Je regarde ce qu'a changé la dernière version. »
- **Aucun reproche**, ni à la personne ni à l'auteur de l'outil : on cherche ce qui a permis le problème, pas un coupable.
- **Ne jamais demander de données réelles** : « Pouvez-vous me montrer un exemple avec des noms inventés ? » ; si la personne colle des données de personnes, ne pas les reprendre et lui rappeler la règle avec bienveillance.
- **Donner un contournement** dès qu'il existe : « En attendant, vous pouvez… »

## Questions toutes prêtes

- « Est-ce que des personnes sont bloquées en ce moment ? » *(pour savoir s'il faut d'abord revenir à la version précédente)*
- « Qu'est-ce qui a changé juste avant que ça ne marche plus ? » *(le dernier changement est souvent la cause)*
- « Est-ce que ça arrive à tout le monde, ou à une seule personne ? » *(pour savoir si c'est l'outil ou le poste)*
- « Pouvez-vous me copier le message d'erreur, sans données de personnes ? » *(pour chercher la cause exacte)*
- « Des informations sur des personnes ont-elles pu être vues, perdues ou modifiées ? » *(si oui, il faut prévenir le DPO rapidement ; je vous aide à écrire le message)*
- Évolution : « Qu'est-ce qui changera pour les utilisateurs ? » ; « Comment saura-t-on que c'est réussi ? »
- Reprise : « Qui connaît encore cet outil ? » ; « Où se trouve-t-il exactement ? »

## Messages types

**Aux utilisateurs, incident en cours :**
« L'outil <nom> ne fonctionne pas correctement depuis <moment>. Nous revenons à la version précédente ; en attendant, <contournement>. Nous vous prévenons dès que c'est réglé. »

**Aux utilisateurs, incident réglé :**
« L'outil <nom> fonctionne de nouveau (version <x.y.z>). <Une phrase sur ce qui a été corrigé.> Si vous constatez encore un problème, prévenez <référent, par fonction>. »

**À la cellule opérationnelle :**
« Incident <bloquant / gênant> sur <nom> v<version> depuis <moment>. Retour arrière : <fait / impossible>. Cause probable : <…>. Correction prévue : <…>. Données de personnes concernées : <non / oui, DPO prévenu le …>. »

**Au DPO (données de personnes en jeu) :** les faits seulement, sans aucune donnée de personne dans le message : quel outil, quelles catégories de données, combien de personnes à peu près, depuis quand, ce qui a été fait pour arrêter la fuite ou la perte, qui contacter.

## Message de fin

Court, dans cet ordre : ce qui est réglé · ce qui a été fait pour que ça ne revienne pas (le test ajouté) · ce qui reste à faire et par qui · ce qui a été noté dans le dossier (version, journal des incidents, exceptions) · la prochaine étape proposée.
