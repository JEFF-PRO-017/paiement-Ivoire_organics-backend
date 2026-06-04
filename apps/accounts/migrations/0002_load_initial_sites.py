from django.db import migrations
import uuid

def load_sites(apps, schema_editor):
    Site = apps.get_model('accounts', 'Site')
    
    sites = [
        {
            'nom': 'LARABIA',
        },
        {
            'nom': 'MONGAHA',
        },
        {
            'nom': 'KATIOFI',
        }
    ]
    for site_data in sites:
        Site.objects.get_or_create(defaults=site_data)

def reverse_load_sites(apps, schema_editor):
    Site = apps.get_model('accounts', 'Site')
    site_names = ['LARABIA', 'MONGAHA', 'KATIOFI']
    Site.objects.filter(nom__in=site_names).delete()    


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(load_sites, reverse_code=reverse_load_sites)
    ]