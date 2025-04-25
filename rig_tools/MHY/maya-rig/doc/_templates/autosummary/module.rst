{{ fullname | escape | underline }}

.. rubric:: Description

.. automodule:: {{ fullname }}

.. currentmodule:: {{ fullname }}


{% if functions %}
.. rubric:: Functions

.. autosummary::
    :toctree: .

    {% for function in functions %}
    {{ function }}
    {% endfor %}

{% endif %}

{% if classes %}
.. rubric:: Classes

.. autosummary::
    :toctree: .

    {% for class in classes %}
    {{ class }}
    {% endfor %}

{% endif %}

