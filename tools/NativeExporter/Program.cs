using CodeWalker.GameFiles;
using System.Xml;

if (args.Length != 2)
    throw new ArgumentException("Usage: NativeExporter <sources/cwxml> <hw_weapons/stream>");
var source = Path.GetFullPath(args[0]);
var destination = Path.GetFullPath(args[1]);
Directory.CreateDirectory(destination);
RpfManager.IsGen9 = false; // FiveM GTA V Legacy, version 165 YDR and version 13 YTD.
int drawables = 0;
foreach (var input in Directory.GetFiles(source, "*.ydr.xml").Order())
{
    var name = Path.GetFileName(input).Replace(".ydr.xml", "");
    var originalXml = File.ReadAllText(input);
    var drawable = XmlYdr.GetYdr(originalXml, Path.Combine(source, name));
    var bytes = drawable.Save();
    if (System.Text.Encoding.ASCII.GetString(bytes, 0, 4) != "RSC7")
        throw new Exception("Not a native RSC7 resource: " + name);
    var check = new YdrFile();
    check.Load(bytes);
    if (check.Drawable?.DrawableModels?.High == null || check.Drawable.DrawableModels.High.Length == 0)
        throw new Exception("Failed to decode geometry: " + name);
    var roundtrip = YdrXml.GetXml(check);
    var before = new XmlDocument(); before.LoadXml(originalXml);
    var after = new XmlDocument(); after.LoadXml(roundtrip);
    foreach (var xpath in new[] { "//Geometries/Item", "//Skeleton/Bones/Item", "//Shaders/Item" })
        if (before.SelectNodes(xpath)!.Count != after.SelectNodes(xpath)!.Count)
            throw new Exception("Roundtrip structure mismatch " + xpath + ": " + name);
    foreach (XmlElement vb in after.SelectNodes("//VertexBuffer/Data")!)
        if (string.IsNullOrWhiteSpace(vb.InnerText))
            throw new Exception("Empty decoded vertex buffer: " + name);
    File.WriteAllBytes(Path.Combine(destination, name + ".ydr"), bytes);
    var validation = Path.Combine(source, "..", "native_validation");
    Directory.CreateDirectory(validation);
    File.WriteAllText(Path.Combine(validation, name + ".roundtrip.xml"), roundtrip);
    Console.WriteLine($"PASS {name}.ydr: {bytes.Length} bytes, native decode / geometry / shaders / skeleton verified");
    drawables++;
}
foreach (var input in Directory.GetFiles(source, "*.ytd.xml"))
{
    var name = Path.GetFileName(input).Replace(".ytd.xml", "");
    var texture = XmlYtd.GetYtd(File.ReadAllText(input), Path.Combine(source, name));
    var bytes = texture.Save();
    var check = new YtdFile(); check.Load(bytes);
    if (check.TextureDict?.Textures?.data_items?.Length != 33)
        throw new Exception("Expected 33 separate material texture maps");
    foreach(var map in check.TextureDict.Textures.data_items)
        if (map.Width != 512 || map.Height != 512 || map.Levels != 10)
            throw new Exception("Decoded material dimensions or mip levels mismatch");
    File.WriteAllBytes(Path.Combine(destination, name + ".ytd"), bytes);
    Console.WriteLine($"PASS {name}.ytd: {bytes.Length} bytes, native texture dictionary decode verified");
}
foreach (var input in Directory.GetFiles(source, "*.ycd.xml"))
{
    var name = Path.GetFileName(input).Replace(".ycd.xml", "");
    var original = XmlYcd.GetYcd(File.ReadAllText(input));
    var bytes = original.Save();
    var check = new YcdFile(); RpfFile.LoadResourceFile(check, bytes, 46);
    if (check.ClipMapEntries?.Length != 2 || check.AnimMapEntries?.Length != 2)
        throw new Exception("Expected two custom strike clips and two animations");
    foreach(var entry in check.AnimMapEntries)
    {
        var anim = entry.Animation;
        if (anim.BoneIds.data_items.Length != 42 || anim.Frames < 60)
            throw new Exception("Authored animation tracks/frames missing");
        foreach(var sequence in anim.Sequences.data_items)
        foreach(var track in sequence.Sequences)
        for(int frame=0;frame<sequence.NumFrames;frame++)
        {
            var q=track.EvaluateQuaternion(frame);
            if(Math.Abs(q.Length()-1)>0.001)throw new Exception("Non-unit decoded animation quaternion");
        }
    }
    File.WriteAllBytes(Path.Combine(destination, name+".ycd"),bytes);
    var validation=Path.Combine(source,"..","native_validation");Directory.CreateDirectory(validation);
    File.WriteAllText(Path.Combine(validation,name+".roundtrip.xml"),YcdXml.GetXml(check));
    Console.WriteLine($"PASS {name}.ycd: {bytes.Length} bytes; two authored clips, 42 tracks and all frame quaternions decoded");
}
if (drawables != 8) throw new Exception($"Expected five weapons and three magazines, got {drawables}");
