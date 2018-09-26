
import hashlib




def md5(target):

    import hashlib
    h1 = hashlib.md5()
    h1.update(target.encode('ascii'))
    s2 = h1.hexdigest()
    print(s2)
    return s2
md5(md5('hwz5980279'))

'df4c77661c31b283f1033c4e3bd53683'