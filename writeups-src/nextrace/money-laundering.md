#  Challenge Write-Up: Money laundering

**Author** : 0xsila  X dhia 

##  Challenge Name
**Money laundering**

## Challenge Description :

> i have a lot of cash , i need to clear it  
> can u help me ?  
    

## SOLUTION :

- the cash word was a hint about cache ( CDN cache ) , websites use caching servers to help their servers and make the UX more easy , by caching responses of request based on key , that expect that the user will use a lot of times .

- PURGE method is the method used to clear the cache , this method suppoesed to be protected and forbidden to normal users .

- try using the method , and yes get an 403 Forbidden .
- but thinking like a hacker , any 403 we will try to bypass it .
- after a small vibe hacking or googleing , we will find that there a lot of methods to bypass that .
- one of them is using the header : `x-http-method-overrid`
- this header is acceptable by a lot of proxy servers , this header will overrid the request method and use his value .
- so the proxy will check for the request method in the request , he will see that it is a GET request , so its ok , but he forget to checks headers .

- final exploit : 
add the header `x-http-method-overrid:PURGE`



**flag :**
nexus{D0nt_l3tt_th3m_cl34n_ur_C4Ch3}
