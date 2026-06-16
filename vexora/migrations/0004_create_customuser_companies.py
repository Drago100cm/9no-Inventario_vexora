from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vexora', '0003_subscription_user_fix'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS vexora_customuser_companies (
                    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    customuser_id BIGINT NOT NULL,
                    company_id BIGINT NOT NULL,
                    UNIQUE KEY customuser_company_unique (customuser_id, company_id),
                    KEY customuser_id_idx (customuser_id),
                    KEY company_id_idx (company_id),
                    CONSTRAINT fk_customuser_companies_customuser FOREIGN KEY (customuser_id) REFERENCES vexora_customuser(id) ON DELETE CASCADE,
                    CONSTRAINT fk_customuser_companies_company FOREIGN KEY (company_id) REFERENCES vexora_company(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            """,
            reverse_sql="""
                DROP TABLE IF EXISTS vexora_customuser_companies;
            """,
        ),
    ]
