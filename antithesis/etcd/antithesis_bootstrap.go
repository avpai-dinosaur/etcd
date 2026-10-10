// Copied into server/etcdmain/ by antithesis/Dockerfile at build time only.
// It is not part of the etcd source tree.

package etcdmain

import "github.com/antithesishq/antithesis-sdk-go/assert"

func init() {
	// Bootstrap property: proves the SDK is linked and cataloging works.
	assert.Reachable("etcd server process started", nil)
}
