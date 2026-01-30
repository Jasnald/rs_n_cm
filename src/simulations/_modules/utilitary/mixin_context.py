# -*- coding: utf-8 -*-
# mixins_context.py

class ContextMixin(object):
    """Propaga model, t_part e instance_name a objetos (recursivamente)."""

    _CTX_ATTRS = ('model', 't_part', 'instance_name',
                  'remove_region', 'ZX', 'ZY',
                  'comprimento', 'mesh_size',
                  'output_dir')

    # ---------- nível 0 : fixar contexto na própria instância ----------
    def bind_context(self, model=None, t_part=None, instance_name=None):
        if model         is not None: self.model         = model
        if t_part        is not None: self.t_part        = t_part
        if instance_name is not None: self.instance_name = instance_name

    # ---------- nível 1 + : propagar a outros objetos -------------------
    def propagate_to(self, *targets, **kw):
        """
        Propaga o contexto a *targets* e a todos os sub-objetos que também
        herdem de ContextMixin (profundidade ilimitada).
        Uso permanece:  self.propagate_to(obj1, obj2, …)
        """
        deep     = kw.get('deep', True)      # permite desligar a recursão
        visited  = set()                     # evita loops/ciclos

        def _copy_ctx(src, dst):
            for attr in self._CTX_ATTRS:
                if hasattr(src, attr):
                    # copia SEMPRE, mesmo que o atributo já exista em dst
                    setattr(dst, attr, getattr(src, attr))

        def _walk(src, dst):
            if dst is None or id(dst) in visited:
                return
            visited.add(id(dst))

            _copy_ctx(src, dst)

            # desce na árvore de atributos somente se deep == True
            if deep:
                for sub in getattr(dst, '__dict__', {}).values():
                    if isinstance(sub, ContextMixin):
                        _walk(src, sub)

        for tgt in targets:
            _walk(self, tgt)