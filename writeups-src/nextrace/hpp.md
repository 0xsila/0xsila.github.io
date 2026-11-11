#  Challenge Write-Up: HPP

**Author** : 0xsila 

##  Challenge Name
**HPP**

## Challenge Description :
polution is a big problem in the world ....  
can it reached the HTTP ?  
can u read the secret book and get the flag ? 

## SOLUTION :

HPP : HTTP Parameter Polution , is a really good idea to bypass restriction , specially in IDOR bugs .

access to id=1 => 403 Forbidden
access to id=3 => 200 OK

**bypass :** ?id=2&id=1 => bom get the flag

**flag :**
nexus{HTTP_p4r4m3t3r_p0lut10n_b000000000000m}
