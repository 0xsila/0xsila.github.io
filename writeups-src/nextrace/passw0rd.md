#  Challenge Write-Up: Passw0rd

**Author** : 0xsila 

##  Challenge Name
**Passw0rd**

## Challenge Description :
 > oh , i forgot my password ......
 > lets see what we will get in the response ....
 > maybe changing something will let us breack the logic .....

## SOLUTION :

- eneter any random password .
- click enter , with proxy open in burp .
- intercept the response of the request that check the password .
- change false => true .
- and bom get the flag .



**flag :**
nexus{R3sp0ns3_M4n1pul4Ti0n_is_P0werFull}
