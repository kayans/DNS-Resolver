import dns
import dns.resolver
import dns.query
import dns.name
import dns.message
import dns.rdatatype
import time
import sys

class DNSCache:
    """
    Implement Cache machanism
    """
    def __init__(self, ttl=300):
        self.cache = {}
        self.ttl = ttl  # set up ttl

    def set(self, key, value):
        self.cache[key] = (value, time.time())

    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
        return None

def recursive_resolver(domain, type):
    """
    Dns resolver for hadling recursive query
    """
    try:
        
        answers = dns.resolver.resolve(domain, type)
        
        results = []
        for answer in answers:
            results.append(answer.to_text())

        return results
    
    # Error handling
    except Exception as e:
        print(f"Error occurs while handling {domain}: {e}")
        
    return None
    
def iterative_resolver(domain_name, type, cache):
    """
    Dns resolver for iterative query
    """
    # check exist record in cache
    cached_result = cache.get((domain_name, type))
    if cached_result:
        return cached_result
    # DNS root server
    # root_servers = [
    #     '198.41.0.4', '199.9.14.201', '192.33.4.12',
    #     '199.7.91.13', '192.203.230.10', '192.5.5.241',
    #     '192.112.36.4', '198.97.190.53', '192.36.148.17',
    #     '192.58.128.30', '193.0.14.129', '199.7.83.42',
    #     '202.12.27.33'
    # ]
    dns_server = "8.8.4.4"

    current_ns = [dns_server]
    while True:
        for ns in current_ns:
            try:
                query = dns.message.make_query(domain_name, type)
                response = dns.query.udp(query, ns, timeout=5)

                # if aswer exist
                if len(response.answer) > 0:
                    for ans in response.answer:
                        if ans.rdtype == dns.rdatatype.CNAME:
                            # if type is cname, continue to resolve it
                            cname_target = ans[0].target
                            return iterative_resolver(str(cname_target), type, cache)
                        else:
                            cache.set((domain_name, type), response.answer)
                            return response.answer
                
                # turn to NS server in the next layer
                next_ns = []
                for rrset in response.additional:
                    if rrset.rdtype == dns.rdatatype.A:
                        next_ns.extend([rr.to_text() for rr in rrset])

                if len(next_ns) > 0:
                    current_ns = next_ns
                    break
            # Error handling
            except Exception as e:
                print(f"Error occurs while handling {ns}：{e}")
                sys.exit()

    return None

def main():
    # query initialization
    if len(sys.argv) < 2:
        print("Please specify the domain you want to resolve.")
        sys.exit(1)

    domain = sys.argv[1]
    type = "A"
    cache = DNSCache(ttl=300)  # initialize a cache 
    
    # iterative query handling
    answers_iter = iterative_resolver(domain, type, cache)
    # recursive query handling
    answers_recur = recursive_resolver(domain, type)

    if answers_iter:
        for answer in answers_iter:
            print("Iterative dns resolver:   ",answer)
    else:
        print("Iterative dns resolver didn't find answer.\n")

    if answers_recur:
        for result in answers_recur:
            print("Recursive dns resolver:   ",answer)
    else:
        print("Recursive dns resolver didn't find answer.\n")
        
if __name__ == "__main__":
    main()