-- ACADEMIX Module Comptabilite v2 -- executer UNE SEULE FOIS

CREATE TABLE IF NOT EXISTS `type_frais` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nom` VARCHAR(100) NOT NULL,
  `montant_total` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `description` TEXT DEFAULT NULL,
  `actif` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`), UNIQUE KEY `nom` (`nom`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `configuration_tranches` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `type_frais_id` INT NOT NULL,
  `nom_tranche` VARCHAR(100) NOT NULL,
  `montant` DECIMAL(12,2) NOT NULL,
  `ordre` INT NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`), KEY `fk_ct_tf` (`type_frais_id`),
  CONSTRAINT `fk_ct_tf` FOREIGN KEY (`type_frais_id`) REFERENCES `type_frais`(`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `remises_eleve` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `eleve_id` CHAR(32) NOT NULL,
  `type_frais_id` INT NOT NULL,
  `montant_remise` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `motif` VARCHAR(255) DEFAULT NULL,
  `annee_scolaire` VARCHAR(20) NOT NULL DEFAULT '2025-2026',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_remise` (`eleve_id`, `type_frais_id`, `annee_scolaire`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `paiements` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `eleve_id` CHAR(32) NOT NULL,
  `type_frais_id` INT NOT NULL,
  `tranche_id` INT DEFAULT NULL,
  `montant` DECIMAL(12,2) NOT NULL,
  `recu_num` VARCHAR(50) NOT NULL UNIQUE,
  `notes` TEXT DEFAULT NULL,
  `annee_scolaire` VARCHAR(20) NOT NULL DEFAULT '2025-2026',
  `annule` TINYINT(1) NOT NULL DEFAULT 0,
  `annule_motif` VARCHAR(255) DEFAULT NULL,
  `annule_at` DATETIME DEFAULT NULL,
  `date_paiement` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_pmt_eleve` (`eleve_id`), KEY `fk_pmt_tf` (`type_frais_id`), KEY `fk_pmt_tr` (`tranche_id`),
  CONSTRAINT `fk_pmt_tf` FOREIGN KEY (`type_frais_id`) REFERENCES `type_frais`(`id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_pmt_tr` FOREIGN KEY (`tranche_id`) REFERENCES `configuration_tranches`(`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `depenses` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `motif` VARCHAR(255) NOT NULL,
  `montant` DECIMAL(12,2) NOT NULL,
  `categorie` VARCHAR(100) DEFAULT 'General',
  `date_depense` DATE NOT NULL,
  `notes` TEXT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `clotures_caisse` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `date_cloture` DATE NOT NULL UNIQUE,
  `total_recettes` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `total_depenses` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `solde` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `notes` TEXT DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT IGNORE INTO `type_frais` (`nom`,`montant_total`,`description`) VALUES
  ('Scolarite',75000,'Frais de scolarite annuels'),
  ('Bibliotheque',5000,'Acces bibliotheque scolaire'),
  ('Cantine',30000,'Repas a la cantine');
INSERT IGNORE INTO `configuration_tranches`(`type_frais_id`,`nom_tranche`,`montant`,`ordre`) SELECT id,'Tranche 1',25000,1 FROM `type_frais` WHERE `nom`='Scolarite';
INSERT IGNORE INTO `configuration_tranches`(`type_frais_id`,`nom_tranche`,`montant`,`ordre`) SELECT id,'Tranche 2',25000,2 FROM `type_frais` WHERE `nom`='Scolarite';
INSERT IGNORE INTO `configuration_tranches`(`type_frais_id`,`nom_tranche`,`montant`,`ordre`) SELECT id,'Tranche 3',25000,3 FROM `type_frais` WHERE `nom`='Scolarite';
INSERT IGNORE INTO `configuration_tranches`(`type_frais_id`,`nom_tranche`,`montant`,`ordre`) SELECT id,'Paiement unique',5000,1 FROM `type_frais` WHERE `nom`='Bibliotheque';
INSERT IGNORE INTO `configuration_tranches`(`type_frais_id`,`nom_tranche`,`montant`,`ordre`) SELECT id,'Semestre 1',15000,1 FROM `type_frais` WHERE `nom`='Cantine';
INSERT IGNORE INTO `configuration_tranches`(`type_frais_id`,`nom_tranche`,`montant`,`ordre`) SELECT id,'Semestre 2',15000,2 FROM `type_frais` WHERE `nom`='Cantine';