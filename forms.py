from django import forms

from models import PurpleRobotReading

class ExportJobForm(forms.Form):
    start_date = forms.DateTimeField()  
    end_date = forms.DateTimeField()

    destination = forms.EmailField()
    
    def __init__(self, *args, **kwargs):
        super(ExportJobForm, self).__init__(*args, **kwargs)
        
        probes = []
        
        for probe in PurpleRobotReading.objects.order_by('probe').values_list('probe', flat=True).distinct():
            tokens = probe.split('.')
            
            probes.append((probe, tokens[-1]))

        self.fields['probes'] = forms.MultipleChoiceField(choices=probes, widget=forms.CheckboxSelectMultiple())

        hashes = []

        for user_hash in PurpleRobotReading.objects.order_by('user_id').values_list('user_id', flat=True).distinct():
            hashes.append((user_hash, user_hash))

        self.fields['hashes'] = forms.MultipleChoiceField(choices=hashes, widget=forms.CheckboxSelectMultiple())
