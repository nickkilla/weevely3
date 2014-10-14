from core.vectors import PhpCode, ShellCmd
from core.module import Module
from core.loggers import log
from core import messages
import random


class Perms(Module):

    """Find files with given write, read, or execute permission."""

    def init(self):

        self.register_info(
            {
                'author': [
                    'Emilio Pinna'
                ],
                'license': 'GPLv3'
            }
        )

        self.register_vectors(
            [
            # Don't be scared of the side, the PHP payloads are automatically minified
            PhpCode(
              payload = """
function ckprint($df,$t,$a) {
    if(@file_exists($df)&&cktp($df,$t)&&@ckattr($df,$a)) {
        print($df.PHP_EOL);
        return True;
    }
}

function ckattr($df, $a) {
    $w=strstr($a,"w");
    $r=strstr($a,"r");
    $x=strstr($a,"x");
    return ($a=='')||(!$w||is_writable($df))&&(!$r||is_readable($df))&&(!$x||is_executable($df));
}

function cktp($df, $t) {
    return ($t==''||($t=='f'&&@is_file($df))||($t=='d'&&@is_dir($df)));
}

function swp($fdir, $d, $t, $a, $q, $r){
    if($d==$fdir && ckprint($d,$t,$a) && ($q!="")) return;

    $h=@opendir($d);
    while ($f = @readdir($h)) {
        if(substr($fdir,0,1)=='/') {
            $df='/';
        } else {
            $df='';
        }

        $df.=join('/', array(trim($d, '/'), trim($f, '/')));

        if(($f!='.')&&($f!='..')&&ckprint($df,$t,$a) && ($q!="")) return;
        if(($f!='.')&&($f!='..')&&cktp($df,'d')&&$r) @swp($fdir, $df, $t, $a, $q, $r);
    }
    if($h) closedir($h);
}

swp('${rpath}','${rpath}','${ type if type == 'd' or type == 'f' else '' }','${ '%s%s%s' % (('w' if writable else ''), ('r' if readable else ''), ('x' if executable else '') ) }','${ '1' if quit else '' }', ${not no_recursion});
""",
             name = 'php_recursive'
            ),
            ShellCmd(
              payload = """find ${rpath} ${ '-maxdepth 1' if no_recursion else '' } ${ '-print -quit' if quit else '' } ${ '-writable' if writable else '' } ${ '-readable' if readable else '' } ${ '-executable' if executable else '' } ${ '-type %s' % (type) if type == 'd' or type == 'f' else '' }""",
              name = "sh_find",
              arguments = [
                "-stderr_redirection",
                " 2>/dev/null",
              ]
            )
            ]
        )

        self.register_arguments([
          { 'name' : 'rpath', 'help' : 'Starting path' },
          { 'name' : '-quit', 'action' : 'store_true', 'default' : False, 'help' : 'Quit at first result' },
          { 'name' : '-writable', 'action' : 'store_true' },
          { 'name' : '-readable', 'action' : 'store_true' },
          { 'name' : '-executable', 'action' : 'store_true' },
          { 'name' : '-no-recursion', 'action' : 'store_true', 'default' : False },
          { 'name' : '-vector', 'choices' : self.vectors.get_names(), 'default' : 'php_recursive' },
        ])

    def run(self, args):
        result = self.vectors.get_result(args['vector'], args)
        return result.split('\n') if isinstance(result,str) else result

    def print_result(self, result):
        if result: log.info('\n'.join(result))