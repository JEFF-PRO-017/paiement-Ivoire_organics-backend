from django.db import migrations

def load_sites(apps, schema_editor):
    Site = apps.get_model('accounts', 'Site')
    
    sites = ['LARABIA', 'MONGAHA', 'KATIOFI']
    
    for nom in sites:
        Site.objects.get_or_create(nom=nom)

def reverse_load_sites(apps, schema_editor):
    Site = apps.get_model('accounts', 'Site')
    Site.objects.filter(nom__in=['LARABIA', 'MONGAHA', 'KATIOFI']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(load_sites, reverse_code=reverse_load_sites)
    ]