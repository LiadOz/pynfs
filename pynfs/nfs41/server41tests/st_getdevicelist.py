from pynfs.nfscommon.xdrdef.nfs4_const import *
from pynfs.nfscommon.xdrdef.nfs4_type import *
from .environment import check, fail, use_obj, open_file, create_file, get_blocksize
from pynfs.nfscommon import nfs_ops
op = nfs_ops.NFS4ops()
from pynfs.nfs41.block import Packer as BlockPacker, Unpacker as BlockUnpacker, \
    PNFS_BLOCK_INVALID_DATA, PNFS_BLOCK_READWRITE_DATA, \
    pnfs_block_layoutupdate4
from pynfs.nfs41.nfs4lib import state00

def testGetDevList(t, env):
    """Check devlist

    FLAGS: pnfs
    CODE: GETDLIST1
    """
    sess = env.c1.new_pnfs_client_session(env.testname(t))
    # Test that fs handles block layouts
    ops = use_obj(env.opts.path) + [op.getattr(1<<FATTR4_FS_LAYOUT_TYPES)]
    res = sess.compound(ops)
    check(res)
    if FATTR4_FS_LAYOUT_TYPES not in res.resarray[-1].obj_attributes:
        fail("fs_layout_type not available")
    for lo_type in res.resarray[-1].obj_attributes[FATTR4_FS_LAYOUT_TYPES]:
        # Send GETDEVICELIST
        ops = use_obj(env.opts.path) + [op.getdevicelist(lo_type, 0xffffffff, 0, "")]
        res = sess.compound(ops)
        check(res)
        # STUB - check block stuff
        dev_list = res.resarray[-1].gdlr_deviceid_list
        print(dev_list)

def testGetDevInfo(t, env):
    """Check devlist

    FLAGS: pnfs
    DEPEND: GETDLIST1
    CODE: GETDINFO1
    """
    sess = env.c1.new_pnfs_client_session(env.testname(t))
    # Test that fs handles block layouts
    ops = use_obj(env.opts.path) + [op.getattr(1<<FATTR4_FS_LAYOUT_TYPES)]
    res = sess.compound(ops)
    check(res)
    if FATTR4_FS_LAYOUT_TYPES not in res.resarray[-1].obj_attributes:
        fail("fs_layout_type not available")
    for lo_type in res.resarray[-1].obj_attributes[FATTR4_FS_LAYOUT_TYPES]:
        # Send GETDEVICELIST
        lo_type = LAYOUT4_BLOCK_VOLUME
        ops = use_obj(env.opts.path) + [op.getdevicelist(lo_type, 0xffffffff, 0, "")]
        res = sess.compound(ops)
        check(res)
        dev_list = res.resarray[-1].gdlr_deviceid_list
        p = BlockUnpacker("")
        for dev_id in dev_list:
            ops = use_obj(env.opts.path) + [op.getdeviceinfo(dev_id, lo_type, 0xffffffff, 0)]
            res = sess.compound(ops)
            check(res)
            if lo_type==LAYOUT4_BLOCK_VOLUME:
                p.reset(res.resarray[-1].da_addr_body)
                decode = p.unpack_pnfs_block_deviceaddr4()
                p.done()
                print(decode)


## def xxxtestLayout(t, env):
##     """Verify layout handling

##     FLAGS: pnfs
##     CODE: GETLAYOUT1
##     """
##     sess = env.c1.new_pnfs_client_session(env.testname(t))
##     blocksize = get_blocksize(sess, use_obj(env.opts.path))
##     # Open the file
##     owner = "owner for %s" % env.testname(t)
##     # openres = open_file(sess, owner, env.opts.path + ["simple_extent"])
##     openres = open_file(sess, owner, env.opts.path + ["hole_between_extents"])
##     check(openres)
##     # Get a layout
##     fh = openres.resarray[-1].object
##     open_stateid = openres.resarray[-2].stateid
##     ops = [op.putfh(fh),
##            op.layoutget(False, LAYOUT4_BLOCK_VOLUME, LAYOUTIOMODE4_READ,
##                         0, 0xffffffff, 4*blocksize, open_stateid, 0xffff)]
##     res = sess.compound(ops)
##     check(res)
    
def testGetLayout(t, env):
    """Verify layout handling

    FLAGS: pnfs
    CODE: GETLAYOUT1
    """
    sess = env.c1.new_pnfs_client_session(env.testname(t))
    blocksize = get_blocksize(sess, use_obj(env.opts.path))
    # Create the file
    res = create_file(sess, env.testname(t))
    check(res)
    # Get layout
    fh = res.resarray[-1].object
    open_stateid = res.resarray[-2].stateid
    ops = [op.putfh(fh),
           op.layoutget(False, LAYOUT4_BLOCK_VOLUME, LAYOUTIOMODE4_READ,
                        0, 0xffffffffffffffff, 4*blocksize, open_stateid, 0xffff)]
    res = sess.compound(ops)
    check(res)
    # Parse opaque
    for layout in  res.resarray[-1].logr_layout:
        if layout.loc_type == LAYOUT4_BLOCK_VOLUME:
            p = BlockUnpacker(layout.loc_body)
            opaque = p.unpack_pnfs_block_layout4()
            p.done()
            print(opaque)

def testEMCGetLayout(t, env):
    """Verify layout handling

    Debugging test that looks for pre-existing file (server2fs1/dump.eth)
    so we don't have to worry about creating a file.

    FLAGS: 
    CODE: GETLAYOUT100
    """
    sess = env.c1.new_pnfs_client_session(env.testname(t))
    blocksize = get_blocksize(sess, use_obj(env.opts.path))
    # Create the file
    file = ["server2fs1", "dump.eth"]
    res = open_file(sess, env.testname(t), file)
    check(res)
    # Get layout
    fh = res.resarray[-1].object
    stateid = res.resarray[-2].stateid
    stateid.seqid = 0
    ops = [op.putfh(fh),
           op.layoutget(False, LAYOUT4_BLOCK_VOLUME, LAYOUTIOMODE4_READ,
                        0, 0xffffffffffffffff, 4*blocksize, stateid, 0xffff)]
    res = sess.compound(ops)
    check(res)
    # Parse opaque
    for layout in  res.resarray[-1].logr_layout:
        if layout.loc_type == LAYOUT4_BLOCK_VOLUME:
            p = BlockUnpacker(layout.loc_body)
            opaque = p.unpack_pnfs_block_layout4()
            p.done()
            print(opaque)

def testLayoutReturnFile(t, env):
    """
    Return a file's layout
    
    FLAGS: pnfs
    DEPEND: GETLAYOUT1
    CODE: LAYOUTRET1
    """
    sess = env.c1.new_pnfs_client_session(env.testname(t))
    blocksize = get_blocksize(sess, use_obj(env.opts.path))
    # Create the file
    res = create_file(sess, env.testname(t))
    check(res)
    # Get layout
    fh = res.resarray[-1].object
    open_stateid = res.resarray[-2].stateid
    ops = [op.putfh(fh),
           op.layoutget(False, LAYOUT4_BLOCK_VOLUME, LAYOUTIOMODE4_READ,
                        0, 0xffffffffffffffff, 4*blocksize, open_stateid, 0xffff)]
    res = sess.compound(ops)
    check(res)
    # Return layout
    layout_stateid = res.resarray[-1].logr_stateid
    ops = [op.putfh(fh),
           op.layoutreturn(False, LAYOUT4_BLOCK_VOLUME, LAYOUTIOMODE4_ANY,
                           layoutreturn4(LAYOUTRETURN4_FILE,
                                         layoutreturn_file4(0, 0xffffffffffffffff, layout_stateid, "")))]
    res = sess.compound(ops)
    check(res)

def testLayoutReturnFsid(t, env):
    """
    Return all of a filesystem's layouts
    
    FLAGS: pnfs
    DEPEND: GETLAYOUT1
    CODE: LAYOUTRET2
    """
    sess = env.c1.new_pnfs_client_session(env.testname(t))
    blocksize = get_blocksize(sess, use_obj(env.opts.path))
    # Create the file
    res = create_file(sess, env.testname(t))
    check(res)
    # Get layout
    fh = res.resarray[-1].object
    open_stateid = res.resarray[-2].stateid
    ops = [op.putfh(fh),
           op.layoutget(False, LAYOUT4_BLOCK_VOLUME, LAYOUTIOMODE4_READ,
                        0, 0xffffffffffffffff, 4*blocksize, open_stateid, 0xffff)]
    res = sess.compound(ops)
    check(res)
    # Return layout
    ops = use_obj(env.opts.path) + \
          [op.layoutreturn(False, LAYOUT4_BLOCK_VOLUME, LAYOUTIOMODE4_ANY,
                           layoutreturn4(LAYOUTRETURN4_FSID))]
    res = sess.compound(ops)
    check(res)

def testLayoutReturnAll(t, env):
    """
    Return all of a client's layouts
    
    FLAGS: pnfs
    DEPEND: GETLAYOUT1
    CODE: LAYOUTRET3
    """
    sess = env.c1.new_pnfs_client_session(env.testname(t))
    blocksize = get_blocksize(sess, use_obj(env.opts.path))
    # Create the file
    res = create_file(sess, env.testname(t))
    check(res)
    # Get layout
    fh = res.resarray[-1].object
    open_stateid = res.resarray[-2].stateid
    ops = [op.putfh(fh),
           op.layoutget(False, LAYOUT4_BLOCK_VOLUME, LAYOUTIOMODE4_READ,
                        0, 0xffffffffffffffff, 4*blocksize, open_stateid, 0xffff)]
    res = sess.compound(ops)
    check(res)
    # Return layout
    ops = [op.layoutreturn(False, LAYOUT4_BLOCK_VOLUME, LAYOUTIOMODE4_ANY,
                           layoutreturn4(LAYOUTRETURN4_ALL))]
    res = sess.compound(ops)
    check(res)

def testLayoutCommit(t, env):
    """
    Do some commits

    FLAGS: pnfs
    CODE: LAYOUTCOMMIT1
    """
    sess = env.c1.new_pnfs_client_session(env.testname(t))
    blocksize = get_blocksize(sess, use_obj(env.opts.path))
    # Create the file
    res = create_file(sess, env.testname(t))
    check(res)
    # Get layout
    fh = res.resarray[-1].object
    open_stateid = res.resarray[-2].stateid
    ops = [op.putfh(fh),
           op.layoutget(False, LAYOUT4_BLOCK_VOLUME, LAYOUTIOMODE4_RW,
                        0, 4*blocksize, 4*blocksize, open_stateid, 0xffff)]
    res = sess.compound(ops)
    check(res)
    layout_stateid = res.resarray[-1].logr_stateid
    # Parse opaque
    for layout in  res.resarray[-1].logr_layout:
        if layout.loc_type != LAYOUT4_BLOCK_VOLUME:
            fail("Did not get Block layout")
        p = BlockUnpacker(layout.loc_body)
        opaque = p.unpack_pnfs_block_layout4()
        p.done()
        print(opaque)
    final_extent = opaque.blo_extents[-1]
    print(final_extent)
    if final_extent.bex_state != PNFS_BLOCK_INVALID_DATA:
        fail("Expected INVALID_DATA in extent")
    # LAYOUTCOMMIT
    final_extent.bex_state = PNFS_BLOCK_READWRITE_DATA
    p = BlockPacker()
    p.pack_pnfs_block_layoutupdate4(pnfs_block_layoutupdate4([final_extent]))
    notime = newtime4(False)
    ops = [op.putfh(fh),
           op.layoutcommit(final_extent.bex_file_offset,
                           final_extent.bex_length,
                           False, layout_stateid,
                           newoffset4(True, 4 * blocksize - 1),
                           notime,
                           layoutupdate4(LAYOUT4_BLOCK_VOLUME, p.get_buffer()))]
    res = sess.compound(ops)
    check(res)
    print(res)
         
    