from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_user_options_alter_user_region_alter_user_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='allowed_modules',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Lista de módulos que o usuário pode acessar. Vazio = usa padrão do perfil.',
                verbose_name='Módulos permitidos',
            ),
        ),
    ]
