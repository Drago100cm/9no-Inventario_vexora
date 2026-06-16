from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vexora', '0002_payment_user_alter_payment_company'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE vexora_subscription
                ADD COLUMN IF NOT EXISTS user_id bigint(20) NULL;

                UPDATE vexora_subscription s
                JOIN vexora_company c ON s.company_id = c.id
                SET s.user_id = c.owner_id
                WHERE s.user_id IS NULL;

                ALTER TABLE vexora_subscription
                DROP FOREIGN KEY IF EXISTS vexora_subscription_company_id_e02bce15_fk_vexora_company_id;
                ALTER TABLE vexora_subscription
                DROP INDEX IF EXISTS company_id;
                ALTER TABLE vexora_subscription
                DROP COLUMN IF EXISTS company_id;
            """,
            reverse_sql="""
                ALTER TABLE vexora_subscription
                ADD COLUMN IF NOT EXISTS company_id bigint(20) NULL;

                UPDATE vexora_subscription s
                JOIN vexora_company c ON c.owner_id = s.user_id
                SET s.company_id = c.id
                WHERE s.company_id IS NULL;

                ALTER TABLE vexora_subscription
                DROP COLUMN IF EXISTS user_id;
            """,
        ),
    ]
