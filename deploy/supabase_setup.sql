-- Supabase SQL Setup for JDS Serv
-- Führe dieses SQL im Supabase SQL Editor aus

-- Tabelle: Unternehmen
CREATE TABLE IF NOT EXISTS backup_app_company (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabelle: User-Profile (verknüpft Django-User mit einem Unternehmen)
CREATE TABLE IF NOT EXISTS backup_app_userprofile (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    company_id BIGINT REFERENCES backup_app_company(id) ON DELETE CASCADE,
    UNIQUE(user_id)
);

-- Tabelle: Clients (plus Unternehmen-Verknüpfung)
CREATE TABLE IF NOT EXISTS backup_app_client (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT REFERENCES backup_app_company(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    machine_id VARCHAR(255) UNIQUE NOT NULL,
    api_token VARCHAR(255) UNIQUE NOT NULL,
    operating_system VARCHAR(100) DEFAULT '',
    last_seen TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    max_backups INTEGER DEFAULT 30,
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabelle: Backup Jobs
CREATE TABLE IF NOT EXISTS backup_app_backupjob (
    id BIGSERIAL PRIMARY KEY,
    client_id BIGINT REFERENCES backup_app_client(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending',
    total_files INTEGER DEFAULT 0,
    total_size BIGINT DEFAULT 0,
    transferred_size BIGINT DEFAULT 0,
    error_message TEXT DEFAULT '',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Tabelle: Backup Files
CREATE TABLE IF NOT EXISTS backup_app_backupfile (
    id BIGSERIAL PRIMARY KEY,
    backup_job_id BIGINT REFERENCES backup_app_backupjob(id) ON DELETE CASCADE,
    file_path VARCHAR(1024) NOT NULL,
    file_name VARCHAR(512) NOT NULL,
    file_size BIGINT DEFAULT 0,
    file_hash VARCHAR(64) DEFAULT '',
    storage_path VARCHAR(1024) DEFAULT '',
    is_directory BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabelle: Backup Logs (Protokollführung)
CREATE TABLE IF NOT EXISTS backup_app_backuplog (
    id BIGSERIAL PRIMARY KEY,
    client_id BIGINT REFERENCES backup_app_client(id) ON DELETE CASCADE,
    level VARCHAR(20) DEFAULT 'info',
    message TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabelle: Backup Schedules
CREATE TABLE IF NOT EXISTS backup_app_backupschedule (
    id BIGSERIAL PRIMARY KEY,
    client_id BIGINT REFERENCES backup_app_client(id) ON DELETE CASCADE,
    interval_minutes INTEGER DEFAULT 60,
    paths TEXT DEFAULT 'C:\\Users',
    exclude_patterns TEXT DEFAULT '',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabelle: Company Settings (Aufbewahrung max 5 Tage)
CREATE TABLE IF NOT EXISTS backup_app_companysettings (
    id BIGSERIAL PRIMARY KEY,
    company_name VARCHAR(255) DEFAULT 'Mein Unternehmen',
    backup_retention_days INTEGER DEFAULT 5,
    max_file_size_mb INTEGER DEFAULT 500,
    notify_on_failure BOOLEAN DEFAULT TRUE,
    notification_email VARCHAR(254) DEFAULT '',
    storage_limit_gb INTEGER DEFAULT 10,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabelle: DRF Auth Token (für Admin Portal Login)
CREATE TABLE IF NOT EXISTS authtoken_token (
    key VARCHAR(40) PRIMARY KEY,
    created TIMESTAMPTZ DEFAULT NOW(),
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    UNIQUE(user_id)
);

-- Indizes
CREATE INDEX IF NOT EXISTS idx_backupjob_client ON backup_app_backupjob(client_id);
CREATE INDEX IF NOT EXISTS idx_backupjob_status ON backup_app_backupjob(status);
CREATE INDEX IF NOT EXISTS idx_backupjob_started ON backup_app_backupjob(started_at);
CREATE INDEX IF NOT EXISTS idx_backupfile_job ON backup_app_backupfile(backup_job_id);
CREATE INDEX IF NOT EXISTS idx_backuplog_client ON backup_app_backuplog(client_id);
CREATE INDEX IF NOT EXISTS idx_client_company ON backup_app_client(company_id);

-- Standard-Einstellungen (5 Tage Aufbewahrung!)
INSERT INTO backup_app_companysettings (id, company_name, backup_retention_days)
VALUES (1, 'Mein Unternehmen', 5)
ON CONFLICT (id) DO NOTHING;
