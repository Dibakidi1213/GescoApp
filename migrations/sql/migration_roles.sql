-- Migration script pour mettre à jour les rôles utilisateur
-- À exécuter après avoir sauvegardé la base de données

-- Modifier la table users pour rendre school_id nullable
ALTER TABLE users MODIFY COLUMN school_id INT NULL;

-- Ajouter la colonne email
ALTER TABLE users ADD COLUMN email VARCHAR(120) AFTER full_name;

-- Mettre à jour les rôles existants
UPDATE users SET role = 'school_admin' WHERE role = 'admin';
UPDATE users SET role = 'secretary' WHERE role = 'secretaire';
UPDATE users SET role = 'professor' WHERE role = 'professeur';

-- Modifier l'enum des rôles
ALTER TABLE users MODIFY COLUMN role ENUM('super_admin','school_admin','secretary','discipline','professor') NOT NULL;

-- Créer un super admin (à adapter selon vos besoins)
-- INSERT INTO users (username, password_hash, role, full_name, email) VALUES ('superadmin', 'hashed_password', 'super_admin', 'Super Administrateur', 'superadmin@example.com');
