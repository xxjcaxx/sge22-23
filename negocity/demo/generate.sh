#!/bin/bash
	echo '<odoo><data>'

for i in ./small/*
do

  img=$(base64 $i)

	echo '<record id="negocity.character_template_'$i'" model="negocity.character_template">'
	echo '<field name="name">'$i'</field>'
	echo '<field name="image">'"$img"'</field>'
	echo '</record>'
done
	echo '</data></odoo>'
