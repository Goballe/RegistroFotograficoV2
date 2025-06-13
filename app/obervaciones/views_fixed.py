    def get_success_url(self):
        return reverse('obervaciones:ver_observacion', kwargs={
            'proyecto_id': self.kwargs['proyecto_id'],
            'observacion_id': self.kwargs['observacion_id']
        })
