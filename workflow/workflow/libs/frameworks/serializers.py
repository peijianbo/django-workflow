from rest_framework import serializers


class DisplayModelSerializer(serializers.ModelSerializer):
    """
    add an extra field(named field_name+'_display') for describing ChoiceField.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in list(self.fields.items()):
            if isinstance(field, serializers.ChoiceField):
                self.fields[field_name+'_display'] = serializers.CharField(
                    source=f'get_{field_name}_display',
                    read_only=True,
                    label=field.label,
                    help_text=field.help_text
                )
